import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.ml.detector import predict_video

VIDEO_PATH = r"D:\project-exprience-portfolio\2024-vas\watch\processed\v9.mp4"
RUNS = 5


def main():
    print(f"Video: {VIDEO_PATH}")
    print(f"Runs: {RUNS}\n")

    durations = []
    for i in range(RUNS):
        start = time.perf_counter()
        result = predict_video(VIDEO_PATH)
        elapsed = time.perf_counter() - start
        durations.append(elapsed)
        label = "violence" if result["confidence"] >= 0.85 else "non-violence"
        print(f"Run {i + 1}: {elapsed:.3f}s — {label} ({result['confidence']:.3f}) — {result['frame_count']} frames")

    avg = sum(durations) / len(durations)
    fps = result["frame_count"] / avg
    print(f"\nAvg inference time: {avg:.3f}s")
    print(f"Frames processed:   {result['frame_count']}")
    print(f"FPS (avg):          {fps:.2f}")


if __name__ == "__main__":
    main()