from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr, ConfigDict
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.db import get_db
from app.main import limiter
from app.models.user import UserDB, UserOut
from app.repositories.refresh_tokens_repository import RefreshTokensRepository
from app.repositories.users_repository import UsersRepository

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str
    full_name: str


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class TokenOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn, db: AsyncIOMotorDatabase = Depends(get_db)):
    repo = UsersRepository(db)

    if await repo.email_exists(body.email):
        raise HTTPException(status_code=400, detail="email already registered")

    user = UserDB(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    inserted_id = await repo.create(user)

    return UserOut(
        id=inserted_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenOut)
@limiter.limit(settings.rate_limit_login)
async def login(request: Request, body: LoginIn, db: AsyncIOMotorDatabase = Depends(get_db)):
    users = UsersRepository(db)
    tokens = RefreshTokensRepository(db)

    doc = await users.get_by_email(body.email)

    if not doc or not verify_password(body.password, doc["hashed_password"]):
        raise HTTPException(status_code=401, detail="invalid credentials")

    email = doc["email"]
    access = create_access_token(email)
    refresh = create_refresh_token(email)

    await tokens.save(refresh, email)

    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenOut)
async def refresh(body: RefreshIn, db: AsyncIOMotorDatabase = Depends(get_db)):
    tokens = RefreshTokensRepository(db)

    try:
        email = decode_refresh_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid token")

    doc = await tokens.get(body.refresh_token)

    if not doc:
        raise HTTPException(status_code=401, detail="invalid token")

    if doc["revoked"]:
        await tokens.revoke_all_for_user(email)
        raise HTTPException(status_code=401, detail="token reuse detected")

    await tokens.revoke(body.refresh_token)

    new_access = create_access_token(email)
    new_refresh = create_refresh_token(email)
    await tokens.save(new_refresh, email)

    return TokenOut(access_token=new_access, refresh_token=new_refresh)