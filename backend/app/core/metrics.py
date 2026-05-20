from collections import defaultdict

request_counts: dict[str, int] = defaultdict(int)
request_durations: dict[str, float] = defaultdict(float)


def record_request(method: str, path: str, duration_ms: float) -> None:
    key = f"{method}:{path}"
    request_counts[key] += 1
    request_durations[key] = round(duration_ms / 1000, 4)