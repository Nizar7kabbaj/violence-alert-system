from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase


class AuditRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["audit_log"]

    async def log(self, action: str, actor: str, detail: dict) -> None:
        await self.col.insert_one({
            "action": action,
            "actor": actor,
            "detail": detail,
            "timestamp": datetime.utcnow(),
        })

    async def list_entries(
        self,
        skip: int = 0,
        limit: int = 50,
        actor: Optional[str] = None,
        action: Optional[str] = None,
    ) -> list[dict]:
        query = {}
        if actor:
            query["actor"] = actor
        if action:
            query["action"] = action

        cursor = self.col.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)