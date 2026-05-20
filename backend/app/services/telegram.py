import asyncio
import logging
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_BASE = "https://api.telegram.org/bot"
_MAX_ATTEMPTS = 3

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=10)
    return _client


async def close_client() -> None:
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


async def send_violence_alert(
    confidence: float,
    camera_id: str,
    snapshot_path: str | None = None,
) -> None:
    text = (
        f"Violence detected\n"
        f"Camera: {camera_id}\n"
        f"Confidence: {confidence:.1%}"
    )

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            await _send(text, snapshot_path)
            logger.info("Telegram alert sent (attempt %d)", attempt)
            return
        except Exception as exc:
            if attempt < _MAX_ATTEMPTS:
                wait = 2 ** attempt
                logger.warning(
                    "Telegram send failed (attempt %d): %s — retrying in %ds",
                    attempt, exc, wait,
                )
                await asyncio.sleep(wait)
            else:
                logger.error(
                    "Telegram alert failed after %d attempts: %s",
                    _MAX_ATTEMPTS, exc,
                )


async def _send(text: str, snapshot_path: str | None) -> None:
    base = f"{_TELEGRAM_BASE}{settings.telegram_bot_token}"
    chat_id = settings.telegram_chat_id
    client = get_client()

    try:
        if snapshot_path:
            path = Path(snapshot_path)
            if path.exists():
                with path.open("rb") as f:
                    resp = await client.post(
                        f"{base}/sendPhoto",
                        data={"chat_id": chat_id, "caption": text},
                        files={"photo": (path.name, f, "image/jpeg")},
                    )
                    resp.raise_for_status()
                return

        resp = await client.post(
            f"{base}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.error("_send raised %s: %s", type(exc).__name__, exc)
        raise