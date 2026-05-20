from fastapi import Header, HTTPException, Depends, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from app.core.config import settings
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def require_internal_key(x_internal_api_key: str = Header(...)):
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        email = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"email": email}


async def require_admin(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    user = await db["users"].find_one({"email": current_user["email"]})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return current_user