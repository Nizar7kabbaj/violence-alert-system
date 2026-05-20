import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import random
import time
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
    docs = []
    now = datetime.utcnow()
    for i in range(NUM_ALERTS):
        docs.append(
            AlertDB(
                video_path=f"/watch/fake_{i}.mp4",
                confidence=round(random.uniform(0.85, 0.99), 3),
                frame_count=random.randint(30, 300),
                label=random.choice(LABELS),
                camera_id=random.choice(CAMERAS),
                timestamp=now - timedelta(minutes=random.randint(0, 60 * 24 * 7)),
                reviewed=random.random() < 0.7,
            ).model_dump()
        )
    await db["alerts"].insert_many(docs)
    print("Seed done.")

    print("\nRunning benchmark queries (3 runs each, median wins)...\n")
    queries = {
        "list 20 newest (no filter)": lambda: repo.list_alerts(limit=20),
        "filter label=violence": lambda: repo.list_alerts(limit=20, label="violence"),
        "filter camera=cam_entrance": lambda: repo.list_alerts(limit=20, camera_id="cam_entrance"),
        "filter reviewed=False (partial idx)": lambda: repo.list_alerts(limit=20, reviewed=False),
        "count_by_label": lambda: repo.count_by_label(),
        "last_24h_count": lambda: repo.last_24h_count(),
    }

    results = {}
    for name, fn in queries.items():
        await fn()
        runs = []
        for _ in range(20):
            start = time.perf_counter()
            await fn()
            runs.append((time.perf_counter() - start) * 1000)
        runs.sort()
        p50 = runs[10]
        p95 = runs[19]
        results[name] = (p50, p95)
        print(f"  {name:42s} p50={p50:7.2f} ms   p95={p95:7.2f} ms")

    print("\nCleaning up test data...")
    await db["alerts"].delete_many({"video_path": {"$regex": "^/watch/fake_"}})
    print("Done.")

    client.close()
    return results


if __name__ == "__main__":
    asyncio.run(main())