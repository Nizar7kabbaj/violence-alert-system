import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.limiter import limiter
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.repositories.alerts_repository import AlertsRepository
from app.api.alerts import router as alerts_router
from app.api.auth import router as auth_router
from app.api.audit import router as audit_router
from app.api import detect
from app.api.metrics import router as metrics_router

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo = AsyncIOMotorClient(
        settings.mongodb_uri,
        maxPoolSize=50,
        minPoolSize=10,
    )
    app.state.db = app.state.mongo[settings.mongodb_db_name]
    app.state.alerts_repo = AlertsRepository(app.state.db)
    await app.state.alerts_repo.create_indexes()
    from app.repositories.refresh_tokens_repository import RefreshTokensRepository
    app.state.refresh_tokens_repo = RefreshTokensRepository(app.state.db)
    await app.state.refresh_tokens_repo.create_indexes()
    yield
    app.state.mongo.close()


app = FastAPI(
    title="Violence Alert System",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.include_router(alerts_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(detect.router, prefix="/api/v1", tags=["detect"])
app.include_router(metrics_router, prefix="/api/v1")

UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/health")
async def health():
    start = time.monotonic()
    await app.state.db.command("ping")
    db_ping_ms = round((time.monotonic() - start) * 1000, 2)
    return {
        "status": "ok",
        "version": "0.1.0",
        "db_ping_ms": db_ping_ms,
        "uptime_seconds": round(time.time() - startup_time, 1),
    }