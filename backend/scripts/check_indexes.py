import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def main():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    indexes = await db["alerts"].index_information()
    print(json.dumps(indexes, indent=2, default=str))
    client.close()


asyncio.run(main())