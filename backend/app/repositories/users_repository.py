from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import UserDB


class UsersRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db["users"]

    async def get_by_email(self, email: str) -> dict | None:
        return await self.col.find_one({"email": email})

    async def create(self, user: UserDB) -> str:
        doc = user.model_dump()
        result = await self.col.insert_one(doc)
        return str(result.inserted_id)

    async def email_exists(self, email: str) -> bool:
        doc = await self.col.find_one({"email": email}, {"_id": 1})
        return doc is not None