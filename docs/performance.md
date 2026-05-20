# Performance

Notes on what I measured, where, and what the numbers actually mean.

## Setup

I ran everything from my laptop in Marrakesh against MongoDB Atlas free tier (M0).

- Windows 11, Python 3.11, motor 3.4.0
- Cold ping from `/health`: about 47 ms
- The cluster is in Europe. I'm not. That matters.

Scripts I used: `backend/scripts/seed_and_benchmark.py` and `backend/scripts/explain_queries.py`.

## What I tested

I seeded 10,000 fake alerts with random `label`, `camera_id`, `timestamp`, and `reviewed`. Then I ran each query 20 times after one warmup call and recorded p50 and p95. I also ran `cursor.explain()` on the filtered queries to see what Mongo was doing on the server side.

## The indexes

Four of them, created at startup in `AlertsRepository.create_indexes`:

| Index | Why |
|---|---|
| `{timestamp: -1}` | Newest first |
| `{label: 1, timestamp: -1}` | Filter by label, then sort |
| `{camera_id: 1, timestamp: -1}` | Filter by camera, then sort |
| `{timestamp: -1}` partial on `reviewed=False` | Smaller and faster, only indexes unreviewed alerts |

## Server-side numbers (from explain)

| Query | Stage | Index | docsExamined | executionTimeMs |
|---|---|---|---|---|
| `label=violence` sort timestamp | IXSCAN | `label_1_timestamp_-1` | 20 | 0 |
| `camera_id=cam_entrance` sort timestamp | IXSCAN | `camera_id_1_timestamp_-1` | 20 | 0 |
| `reviewed=False` sort timestamp | IXSCAN | `unreviewed_partial` | 20 | 0 |

All three filtered queries use `IXSCAN`, not `COLLSCAN`. Mongo touched 20 documents out of 10,000 to build a 20-row result page. Server-side time was under 1 ms.

## End-to-end numbers (what the client sees)

| Query | p50 | p95 |
|---|---|---|
| 20 newest, no filter | 125.79 ms | 160.01 ms |
| filter label=violence | 125.09 ms | 137.17 ms |
| filter camera=cam_entrance | 125.16 ms | 134.04 ms |
| filter reviewed=False (partial idx) | 125.75 ms | 130.99 ms |
| count_by_label (aggregate) | 66.38 ms | 69.87 ms |
| last_24h_count | 60.44 ms | 69.70 ms |

## Why end-to-end is around 125 ms

My original target was under 50 ms. I wrote that before measuring round-trip time.

Marrakesh to the Atlas region is about 50 to 60 ms one way. A query that returns 20 documents pays for the round-trip to send the query, then waits for the documents to come back. That math: