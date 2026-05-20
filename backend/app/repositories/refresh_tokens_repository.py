from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase


class RefreshTokensRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["refresh_tokens"]

    async def create_indexes(self):
        await self.col.create_index("created_at", expireAfterSeconds=604800)
        await self.col.create_index("token")
        await self.col.create_index("email")

    async def save(self, token: str, email: str) -> None:
        await self.col.insert_one({
            "token": token,
            "email": email,
            "revoked": False,
            "created_at": datetime.utcnow(),
        })

    async def get(self, token: str) -> dict | None:
        return await self.col.find_one({"token": token})

    async def revoke(self, token: str) -> None:
        await self.col.update_one({"token": token}, {"$set": {"revoked": True}})

    async def revoke_all_for_user(self, email: str) -> None:
        await self.col.update_many({"email": email}, {"$set": {"revoked": True}})