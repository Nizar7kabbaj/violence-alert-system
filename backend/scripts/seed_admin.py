import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import hash_password


ADMIN_EMAIL = "admin@vas.com"
ADMIN_PASSWORD = "admin1234"


async def main():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    await db["users"].delete_many({"email": {"$in": [ADMIN_EMAIL, "admin@gmail.com"]}})

    await db["users"].insert_one({
        "email": ADMIN_EMAIL,
        "hashed_password": hash_password(ADMIN_PASSWORD),
        "full_name": "VAS Admin",
        "role": "admin",
        "is_active": True,
        "created_at": datetime.utcnow(),
    })
    print(f"admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    client.close()


asyncio.run(main())