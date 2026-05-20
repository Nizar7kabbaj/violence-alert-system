# Inference FPS Benchmark

**Date:** 2026-05-18  
**Machine:** Windows 11, CPU-only (no GPU)  
**Model:** MobileNetV2, modelnew.h5 (~9MB, trained on Real Life Violence Dataset)  
**Input:** 16 frames sampled from v9.mp4, resized to 128x128 RGB  
**Runs:** 5

## Results

| Run | Time (s) | FPS | Label | Confidence |
|---|---|---|---|---|
| 1 (cold) | 5.194 | 3.08 | violence | 0.850 |
| 2 | 2.861 | 5.59 | violence | 0.850 |
| 3 | 2.840 | 5.63 | violence | 0.850 |
| 4 | 2.864 | 5.59 | violence | 0.850 |
| 5 | 2.737 | 5.85 | violence | 0.850 |

**Avg (all runs):** 3.299s — 4.85 FPS  
**Avg (warm, runs 2–5):** 2.825s — 5.66 FPS

## Notes

**Run 1 is slow due to model loading.** The Keras model loads from disk on first call. In production, `get_model()` is called once at startup via FastAPI lifespan, so the cold load cost is paid once and not per request.

**CPU-only inference.** TensorFlow logs confirm no GPU is available. A CUDA-capable GPU would cut inference time by roughly 5–10x for a model this size.

**FPS measures throughput on sampled frames, not real-time video.** The model processes 16 frames per video, not every frame. At 2.8s per inference on a 30fps video, this system is not suitable for real-time detection. It works for batch processing of uploaded clips or watcher-polled files.

**Threshold:** confidence >= 0.85 triggers a violence alert. All 5 runs hit exactly 0.850 on this clip, confirming the model is deterministic on CPU.