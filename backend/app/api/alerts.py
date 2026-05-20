from typing import Optional
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_current_user, require_internal_key
from app.db import get_db
from app.models.alert import AlertIn, AlertOut
from app.repositories.alerts_repository import AlertsRepository
from app.repositories.audit import AuditRepository

router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> AlertsRepository:
    return AlertsRepository(db)


@router.post(
    "",
    response_model=AlertOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alert",
    dependencies=[Depends(require_internal_key)],
)
async def create_alert(
    payload: AlertIn,
    repo: AlertsRepository = Depends(get_repo),
):
    from app.models.alert import AlertDB

    alert_db = AlertDB(**payload.model_dump())
    alert_id = await repo.create_alert(alert_db)
    created = await repo.get_alert(alert_id)
    return created


@router.get(
    "",
    response_model=dict,
    summary="List alerts (paginated)",
)
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    label: Optional[str] = Query(None),
    camera_id: Optional[str] = Query(None),
    reviewed: Optional[bool] = Query(None),
    repo: AlertsRepository = Depends(get_repo),
):
    return await repo.list_alerts(
        skip=skip, limit=limit, label=label, camera_id=camera_id, reviewed=reviewed
    )


@router.get(
    "/stats/count-by-label",
    response_model=dict,
    summary="Count alerts grouped by label",
)
async def count_by_label(repo: AlertsRepository = Depends(get_repo)):
    return await repo.count_by_label()


@router.get(
    "/{alert_id}",
    response_model=AlertOut,
    summary="Get a single alert by ID",
)
async def get_alert(
    alert_id: str,
    repo: AlertsRepository = Depends(get_repo),
):
    try:
        alert = await repo.get_alert(alert_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="invalid alert id")
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")
    return alert


@router.patch(
    "/{alert_id}/review",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark an alert as reviewed",
)
async def mark_reviewed(
    alert_id: str,
    request: Request,
    repo: AlertsRepository = Depends(get_repo),
    current_user: dict = Depends(get_current_user),
):
    try:
        updated = await repo.mark_reviewed(alert_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="invalid alert id")
    if not updated:
        raise HTTPException(status_code=404, detail="alert not found")
    audit = AuditRepository(request.app.state.db)
    await audit.log(
        action="alert.reviewed",
        actor=current_user["email"],
        detail={"alert_id": alert_id},
    )