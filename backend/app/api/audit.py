from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from app.api.deps import require_admin
from app.repositories.audit import AuditRepository

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_audit_log(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    actor: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    _: dict = Depends(require_admin),
):
    repo = AuditRepository(request.app.state.db)
    entries = await repo.list_entries(skip=skip, limit=limit, actor=actor, action=action)
    return {"count": len(entries), "entries": entries}