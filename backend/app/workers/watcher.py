import asyncio
import logging
import shutil
import sys
from pathlib import Path

import httpx
from decouple import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("watcher")

BASE_URL = config("BASE_URL", default="http://localhost:8000")
WATCHER_EMAIL = config("WATCHER_EMAIL")
WATCHER_PASSWORD = config("WATCHER_PASSWORD")
POLL_INTERVAL = int(config("WATCHER_POLL_INTERVAL", default="10"))

WATCH_DIR = Path(__file__).resolve().parents[3] / "watch"
PROCESSED_DIR = WATCH_DIR / "processed"
FAILED_DIR = WATCH_DIR / "failed"

SUPPORTED = {".mp4", ".avi", ".mkv", ".mov"}


async def login(client: httpx.AsyncClient) -> str:
    resp = await client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": WATCHER_EMAIL, "password": WATCHER_PASSWORD},
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    log.info("Logged in as %s", WATCHER_EMAIL)
    return token


async def submit(client: httpx.AsyncClient, token: str, path: Path) -> dict:
    with path.open("rb") as fh:
        resp = await client.post(
            f"{BASE_URL}/api/v1/detect",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (path.name, fh, "video/mp4")},
            params={"camera_id": "watcher"},
            timeout=120.0,
        )
    resp.raise_for_status()
    return resp.json()


async def process(client: httpx.AsyncClient, token: str, path: Path) -> str:
    try:
        result = await submit(client, token, path)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            log.warning("Token expired, refreshing")
            token = await login(client)
            try:
                result = await submit(client, token, path)
            except Exception as retry_exc:
                log.error("Retry failed for %s: %s", path.name, retry_exc)
                shutil.move(str(path), str(FAILED_DIR / path.name))
                return token
        else:
            log.error("HTTP %s for %s: %s", exc.response.status_code, path.name, exc)
            shutil.move(str(path), str(FAILED_DIR / path.name))
            return token
    except Exception as exc:
        log.error("Unexpected error for %s: %s", path.name, exc)
        shutil.move(str(path), str(FAILED_DIR / path.name))
        return token

    label = result.get("label", "unknown")
    confidence = result.get("confidence", 0.0)
    log.info("%s -> %s (%.2f)", path.name, label, confidence)
    shutil.move(str(path), str(PROCESSED_DIR / path.name))
    return token


async def run() -> None:
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Watching %s (interval: %ss)", WATCH_DIR, POLL_INTERVAL)

    async with httpx.AsyncClient() as client:
        token = await login(client)

        while True:
            files = sorted(
                p for p in WATCH_DIR.iterdir()
                if p.is_file() and p.suffix.lower() in SUPPORTED
            )

            if files:
                log.info("Found %d file(s)", len(files))
                for path in files:
                    token = await process(client, token, path)
            else:
                log.debug("Nothing to process")

            await asyncio.sleep(POLL_INTERVAL)


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.info("Watcher stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()