from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from app.models.alert import AlertDB, AlertOut


class AlertsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["alerts"]

    async def create_indexes(self) -> None:
        await self.collection.create_index([("timestamp", DESCENDING)])
        await self.collection.create_index(
            [("label", ASCENDING), ("timestamp", DESCENDING)]
        )
        await self.collection.create_index(
            [("camera_id", ASCENDING), ("timestamp", DESCENDING)]
        )
        await self.collection.create_index(
            [("timestamp", DESCENDING)],
            name="unreviewed_partial",
            partialFilterExpression={"reviewed": False},
        )

    async def create_alert(self, alert: AlertDB) -> str:
        result = await self.collection.insert_one(alert.model_dump())
        return str(result.inserted_id)

    async def get_alert(self, alert_id: str) -> Optional[AlertOut]:
        doc = await self.collection.find_one({"_id": ObjectId(alert_id)})
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        return AlertOut(**doc)

    async def list_alerts(
        self,
        skip: int = 0,
        limit: int = 20,
        label: Optional[str] = None,
        camera_id: Optional[str] = None,
        reviewed: Optional[bool] = None,
    ) -> dict:
        query: dict = {}
        if label is not None:
            query["label"] = label
        if camera_id is not None:
            query["camera_id"] = camera_id
        if reviewed is not None:
            query["reviewed"] = reviewed

        total = await self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort("timestamp", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        items = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            items.append(AlertOut(**doc))
        return {"total": total, "skip": skip, "limit": limit, "items": items}

    async def mark_reviewed(self, alert_id: str) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {"reviewed": True}},
        )
        return result.modified_count == 1

    async def count_by_label(self) -> dict:
        pipeline = [{"$group": {"_id": "$label", "count": {"$sum": 1}}}]
        result = {}
        async for doc in self.collection.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result

    async def last_24h_count(self) -> int:
        since = datetime.utcnow() - timedelta(hours=24)
        return await self.collection.count_documents({"timestamp": {"$gte": since}})