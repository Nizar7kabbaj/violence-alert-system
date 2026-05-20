from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from jose import JWTError
from app.core.security import decode_access_token


def get_user_from_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[len("Bearer "):]
        try:
            return decode_access_token(token)
        except JWTError:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_remote_address)