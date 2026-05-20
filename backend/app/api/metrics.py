from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
from app.core.metrics import request_counts, request_durations
from app.core.config import settings

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics(request: Request):
    client_ip = request.client.host
    allowed = [ip.strip() for ip in settings.metrics_allowed_ips.split(",")]
    if client_ip not in allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    db = request.app.state.db
    alerts_total = await db["alerts"].count_documents({})

    lines = ["# HELP vas_requests_total Total requests by method and path"]
    lines.append("# TYPE vas_requests_total counter")
    for key, count in request_counts.items():
        method, path = key.split(":", 1)
        lines.append(f'vas_requests_total{{method="{method}",path="{path}"}} {count}')

    lines.append("# HELP vas_request_duration_seconds Last request duration in seconds")
    lines.append("# TYPE vas_request_duration_seconds gauge")
    for key, duration in request_durations.items():
        method, path = key.split(":", 1)
        lines.append(f'vas_request_duration_seconds{{method="{method}",path="{path}"}} {duration}')

    lines.append("# HELP vas_alerts_total Total alerts stored in MongoDB")
    lines.append("# TYPE vas_alerts_total gauge")
    lines.append(f"vas_alerts_total {alerts_total}")

    return "\n".join(lines) + "\n"