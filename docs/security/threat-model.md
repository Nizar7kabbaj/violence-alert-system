# Threat Model — Violence Alert System

**Method:** STRIDE  
**Date:** 2026-05-18  
**Scope:** FastAPI backend, MongoDB Atlas, Telegram alerting, local Docker deployment  
**Out of scope:** Cloud infrastructure (deferred to 2025 phase), client devices

---

## Status key

| Status | Meaning |
|---|---|
| Mitigated | Control is implemented and tested |
| Partial | Control exists but gaps remain |
| Accepted | Risk is known and tolerated at this scale |
| Deferred | Out of scope for this phase |

---

## Spoofing

| # | Threat | Status | Control |
|---|---|---|---|
| S1 | Attacker logs in with stolen credentials | Mitigated | bcrypt cost 12, rate limit 5/min per IP on `/login`, timing-safe comparison |
| S2 | Attacker reuses a stolen JWT access token | Partial | Access tokens expire in 15 minutes. No revocation list for access tokens — only refresh tokens are revocable |
| S3 | Attacker reuses a stolen refresh token | Mitigated | Refresh token rotation on every use. Reuse of a revoked token revokes all tokens for that user |
| S4 | Watcher worker spoofs the backend API | Mitigated | `X-Internal-API-Key` header required on watcher-to-backend calls. Key is a 64-byte random hex value from `.env` |
| S5 | Attacker spoofs email during registration | Accepted | No email verification. Registration is open. Acceptable for an internal system with a known user base |

---

## Tampering

| # | Threat | Status | Control |
|---|---|---|---|
| T1 | Attacker modifies a video file to bypass detection | Accepted | File validation checks magic bytes and content-type but not video content integrity. Accepted — this is not a forensic system |
| T2 | Attacker sends a crafted filename to write outside uploads/ | Mitigated | Path traversal protection rejects filenames with `..` or directory separators. Files saved with `uuid4()` names |
| T3 | Attacker sends extra fields to mass-assign model properties | Mitigated | `ConfigDict(extra='forbid')` on every Pydantic model |
| T4 | Attacker tampers with a JWT payload | Mitigated | Tokens signed with HS256. Signature verified on every request |
| T5 | Attacker modifies audit log entries | Partial | Audit log is append-only in application code. No DB-level write protection on Atlas M0 free tier |

---

## Repudiation

| # | Threat | Status | Control |
|---|---|---|---|
| R1 | User denies performing an action | Mitigated | Audit log records actor (email from JWT), action, target, and timestamp on every state change |
| R2 | Audit log entries are deleted | Partial | 365-day TTL index automatically expires old entries. No immutable storage. Accepted for this phase |
| R3 | Watcher actions are not attributed | Mitigated | Watcher authenticates with its own JWT and appears as its email in the audit log |

---

## Information Disclosure

| # | Threat | Status | Control |
|---|---|---|---|
| I1 | Attacker enumerates valid email addresses via `/login` | Mitigated | Wrong email and wrong password return identical response and take the same time |
| I2 | Stack traces leak in error responses | Mitigated | FastAPI default exception handlers return structured JSON without tracebacks |
| I3 | Secrets leak via environment variables in logs | Mitigated | Structured logs record method, path, status, and duration only. No request bodies or headers logged |
| I4 | Snapshot images accessible without auth | Accepted | Snapshots saved to `backend/uploads/snapshots/`. Directory is not served by the API. Risk is local filesystem access only |
| I5 | MongoDB credentials leak via connection string | Mitigated | URI stored in `.env`, gitignored. Atlas user has readWrite on `vas` database only — not cluster-admin |
| I6 | Telegram bot token leak | Mitigated | Token stored in `.env`, gitignored. Exposure would allow an attacker to read and send messages as the bot |
| I7 | CORS allows unintended origins | Mitigated | `allow_origins` restricted to explicit list from `CORS_ALLOWED_ORIGINS` env var |

---

## Denial of Service

| # | Threat | Status | Control |
|---|---|---|---|
| D1 | Attacker floods `/login` to lock out users | Mitigated | Rate limit 5/min per IP via slowapi |
| D2 | Attacker floods `/detect` to exhaust CPU | Mitigated | Rate limit 10/min per user on `/detect`. Inference runs in `asyncio.to_thread` so it does not block the event loop |
| D3 | Attacker uploads very large files to exhaust disk | Partial | Content-type and magic-byte checks run before saving. No explicit file size limit configured in FastAPI. Deferred |
| D4 | Attacker sends many concurrent requests to exhaust Atlas connections | Accepted | Connection pool capped at `maxPoolSize=50`. Load test confirms pool pressure at 50 concurrent users. Atlas M0 has its own connection limits |
| D5 | Telegram rate limits block alert delivery | Accepted | Telegram allows 30 messages/second to a single chat. Retry with exponential backoff handles transient failures. Documented in `docs/alerting-limitations.md` |

---

## Elevation of Privilege

| # | Threat | Status | Control |
|---|---|---|---|
| E1 | Regular user accesses admin-only endpoints | Mitigated | `require_admin` dependency checks `role == "admin"` from DB on every admin request |
| E2 | Attacker forges a JWT with admin role | Mitigated | Role is not stored in the JWT. Every role check hits the database |
| E3 | Container process runs as root | Mitigated | Dockerfile creates and switches to non-root user before running uvicorn |
| E4 | Attacker gains Atlas cluster-admin via compromised DB user | Mitigated | `vas_app` DB user has readWrite on `vas` database only |

---

## Deferred mitigations

These threats are known and out of scope for this phase.

| Threat | Reason deferred |
|---|---|
| File size limit on uploads | Low risk locally. Would add `python-multipart` config in production |
| Access token revocation | Requires a token blocklist. 15-minute expiry is the accepted tradeoff |
| Immutable audit log | Would need Atlas M10+ or an external append-only store |
| HTTPS enforcement | Docker runs locally. TLS terminates at a reverse proxy in production |
| Email verification on registration | Internal system. Known user base |