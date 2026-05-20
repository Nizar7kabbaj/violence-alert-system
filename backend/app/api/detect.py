import uuid
import asyncio
import cv2
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, Query
from app.api.deps import get_current_user
from app.ml.detector import predict_video
from app.core.config import settings
from app.core.limiter import limiter, get_user_from_token
from app.repositories.alerts_repository import AlertsRepository
from app.models.alert import AlertDB
from app.services.telegram import send_violence_alert
from app.db import get_db

router = APIRouter()

UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"
SNAPSHOTS_DIR = UPLOADS_DIR / "snapshots"
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

MAGIC_BYTES = {
    b"\x00\x00\x00\x18ftyp": "mp4",
    b"\x00\x00\x00\x20ftyp": "mp4",
    b"\x52\x49\x46\x46": "avi",
    b"\x1a\x45\xdf\xa3": "mkv",
}


def _check_magic(header: bytes) -> bool:
    for magic, _ in MAGIC_BYTES.items():
        if header[: len(magic)] == magic:
            return True
    if header[4:8] == b"ftyp":
        return True
    return False


def _extract_snapshot(video_path: str, frame_number: int | None = None) -> str | None:
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    mid = max(0, total // 2)
    target = frame_number if frame_number is not None else mid
    cap.set(cv2.CAP_PROP_POS_FRAMES, target)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None

    label = f"Violence detected — frame {target}"
    h, w = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.6
    thickness = 2
    (tw, th), baseline = cv2.getTextSize(label, font, scale, thickness)
    x = 10
    y = h - 10

    cv2.rectangle(frame, (x - 4, y - th - baseline - 4), (x + tw + 4, y + baseline), (0, 0, 0), -1)
    cv2.putText(frame, label, (x, y - baseline), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    filename = f"{uuid.uuid4().hex}.jpg"
    out_path = SNAPSHOTS_DIR / filename
    cv2.imwrite(str(out_path), frame)
    return f"uploads/snapshots/{filename}"


@router.post("/detect")
@limiter.limit("10/minute", key_func=get_user_from_token)
async def detect_violence(
    request: Request,
    file: UploadFile = File(...),
    camera_id: str = Query(default="manual-upload"),
    current_user: dict = Depends(get_current_user),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="unsupported file type")

    filename_parts = Path(file.filename.replace("\\", "/")).parts
    if ".." in filename_parts or len(filename_parts) > 1:
        raise HTTPException(status_code=400, detail="invalid filename")

    header = await file.read(12)
    if not _check_magic(header):
        raise HTTPException(status_code=400, detail="file content does not match a supported video format")

    await file.seek(0)

    tmp_path = UPLOADS_DIR / f"{uuid.uuid4().hex}{ext}"

    try:
        contents = await file.read()
        tmp_path.write_bytes(contents)

        result = await asyncio.to_thread(predict_video, str(tmp_path))

        label = (
            "violence"
            if result["confidence"] >= settings.detection_threshold
            else "non-violence"
        )

        snapshot_path = None
        alert_id = None

        if label == "violence":
            snapshot_path = await asyncio.to_thread(_extract_snapshot, str(tmp_path))

            db = get_db(request)
            repo = AlertsRepository(db)
            alert_doc = AlertDB(
                video_path=file.filename,
                confidence=result["confidence"],
                frame_count=result["frame_count"],
                label=label,
                camera_id=camera_id,
                snapshot_path=snapshot_path,
                notified=False,
            )
            alert_id = await repo.create_alert(alert_doc)

            asyncio.create_task(send_violence_alert(
                confidence=result["confidence"],
                camera_id=camera_id,
                snapshot_path=snapshot_path,
            ))

        return {
            "confidence": result["confidence"],
            "frame_count": result["frame_count"],
            "label": label,
            "snapshot_path": snapshot_path,
            "alert_id": str(alert_id) if alert_id else None,
        }
    finally:
        if tmp_path.exists():
            tmp_path.unlink()