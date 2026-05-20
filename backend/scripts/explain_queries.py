import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import json
import random
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models.alert import AlertDB
from app.repositories.alerts_repository import AlertsRepository

NUM_ALERTS = 10_000
CAMERAS = ["cam_entrance", "cam_parking", "cam_lobby", "cam_corridor", "cam_exit"]
LABELS = ["violence", "non-violence"]


async def main():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    repo = AlertsRepository(db)
    await repo.create_indexes()

    print(f"Seeding {NUM_ALERTS} fake alerts...")
    now = datetime.utcnow()
    docs = [
        AlertDB(
            video_path=f"/watch/fake_{i}.mp4",
            confidence=round(random.uniform(0.85, 0.99), 3),
            frame_count=random.randint(30, 300),
            label=random.choice(LABELS),
            camera_id=random.choice(CAMERAS),
            timestamp=now - timedelta(minutes=random.randint(0, 60 * 24 * 7)),
            reviewed=random.random() < 0.7,
        ).model_dump()
        for i in range(NUM_ALERTS)
    ]
    await db["alerts"].insert_many(docs)

    explains = {
        "filter label=violence sort timestamp": db["alerts"].find(
            {"label": "violence"}
        ).sort("timestamp", -1).limit(20),
        "filter camera=cam_entrance sort timestamp": db["alerts"].find(
            {"camera_id": "cam_entrance"}
        ).sort("timestamp", -1).limit(20),
        "filter reviewed=False (partial idx)": db["alerts"].find(
            {"reviewed": False}
        ).sort("timestamp", -1).limit(20),
    }

    for name, cursor in explains.items():
        print(f"\n=== {name} ===")
        result = await cursor.explain()
        winning = result["queryPlanner"]["winningPlan"]
        exec_stats = result["executionStats"]
        stage = winning
        while "inputStage" in stage:
            stage = stage["inputStage"]
        print(f"  stage:           {stage.get('stage')}")
        print(f"  indexName:       {stage.get('indexName')}")
        print(f"  nReturned:       {exec_stats['nReturned']}")
        print(f"  totalDocsExamined: {exec_stats['totalDocsExamined']}")
        print(f"  totalKeysExamined: {exec_stats['totalKeysExamined']}")
        print(f"  executionTimeMs: {exec_stats['executionTimeMillis']}")

    print("\nCleaning up...")
    await db["alerts"].delete_many({"video_path": {"$regex": "^/watch/fake_"}})
    client.close()


if __name__ == "__main__":
    asyncio.run(main())