import cv2
import numpy as np
from pathlib import Path
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import DepthwiseConv2D as _DWConv2D

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "modelnew.h5"
INPUT_SIZE = (128, 128)
FRAME_SAMPLE = 16

_model = None


class _CompatDepthwiseConv2D(_DWConv2D):
    def __init__(self, **kwargs):
        kwargs.pop("groups", None)
        super().__init__(**kwargs)


def get_model():
    global _model
    if _model is None:
        _model = load_model(
            str(MODEL_PATH),
            custom_objects={"DepthwiseConv2D": _CompatDepthwiseConv2D},
            compile=False,
        )
    return _model


def predict_video(video_path: str) -> dict:
    model = get_model()
    cap = cv2.VideoCapture(video_path)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total_frames // FRAME_SAMPLE)

    frames = []
    idx = 0
    while len(frames) < FRAME_SAMPLE:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, INPUT_SIZE)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame)
        idx += step

    cap.release()

    if not frames:
        return {"confidence": 0.0, "frame_count": 0}

    batch = np.array(frames, dtype="float32") / 255.0
    preds = model.predict(batch, verbose=0)
    confidence = float(np.mean(preds))

    return {"confidence": confidence, "frame_count": len(frames)}