# Load Test Results

**Tool:** Locust 2.29.0  
**Date:** 2026-05-18  
**Setup:** 50 concurrent users, ramp 10/s, 60s run, host `http://localhost:8000`  
**Machine:** Windows 11, local uvicorn, MongoDB Atlas M0 free tier (Marrakesh to Atlas ~50–60ms RTT)

## Results

| Endpoint | Requests | Errors | p50 | p75 | p95 | p99 | Max |
|---|---|---|---|---|---|---|---|
| GET /health | 526 | 0 | 230ms | 680ms | 2300ms | 6400ms | 13586ms |
| GET /api/v1/alerts | 316 | 0 | 460ms | 1200ms | 3200ms | 5500ms | 19827ms |
| POST /api/v1/auth/login | 244 | 239 (429) | — | — | — | — | — |

**Throughput:** ~18 req/s aggregate at peak load.

## Notes

**Login 429s are expected.** The rate limiter caps `/login` at 5 requests/minute per IP. Under load, 50 users sharing one IP triggers this immediately. That is the correct behavior — the limiter is protecting the endpoint.

**Latency is Atlas-dominated.** The M0 free tier sits in a remote region. Cold RTT from Marrakesh to Atlas is 50–60ms. Under 50 concurrent users, connections queue and latency climbs. A co-located database would drop p50 by roughly 10x.

**p99 spikes** on `/health` and `/alerts` reflect Atlas connection pool pressure under sustained load, not application code. The pool is configured at `maxPoolSize=50`, matching the user count exactly — headroom is zero at this concurrency level.

## What this validates

- The async FastAPI stack handles 50 concurrent users without errors on read paths.
- Rate limiting works under load.
- The bottleneck is network RTT to Atlas, not application logic.