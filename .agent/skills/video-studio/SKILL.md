---
name: video-studio
description: Generates high-quality, dark-mode technical slide presentation videos with AI voiceover narration from structured JSON input files. Use this whenever the user wants to compile a presentation, set up media rendering assets, or update the video automation pipeline.
---

# Video Studio Presentation Generation Skill

When executing video studio creation pipelines, follow these strict architectural instructions and coding practices.

## 1. Core Engineering Design Rules
- **Canvas Blueprint:** Draw 1920x1080 landscape slide frames using `Pillow`. Use background slate `#0F172A`, header blue `#38BDF8`, and text white `#E2E8F0`.
- **Audio Generation:** Render slide text-to-speech narrations asynchronously using the `edge-tts` engine. Use the voice profile `en-US-ChristopherNeural` by default.
- **Sequence Compilation:** Use `moviepy` to dynamically measure the duration length of each slide's audio track. Match the static slide frame display duration to that exact audio length timestamp window before stitching them into a final 24fps H.264 encoded MP4 file.
- **Fail-Safe Font Loading:** Implement explicit try/except blocks falling back to `ImageFont.load_default()` if local truetype font paths like `/usr/share/fonts/` are missing on the local host machine or remote runner environments.

## 2. Directory Mappings & Artifacts
- Save all structural pipeline code blocks in `core/` (`image_engine.py`, `audio_engine.py`, `compiler.py`).
- Keep incoming curriculum lesson JSON files in `scripts/`.
- Maintain the main orchestrator loop execution gateway in `run_pipeline.py`.

## 3. Versioning & Evolution (v1 vs. v2 Roadmap)
Do not break the current deterministic execution flow (v1) when experimenting with ML features (v2).
- **v1 (Current Stable):** Rule-based lip sync (RMS volume mapping), static deterministic layouts, and OpenCV pixel masking for anti-jitter. Must run quickly and predictably on low-spec GitHub Actions runners.
- **v2 (Future ML Pipeline):** To bring the avatar to life (head bobs, emotion, layout choices), we will separate ML inference from rendering. A lightweight ONNX or TFLite CPU-friendly model (or remote API) will process the audio/script *first*, outputting a lightweight `choreography.json`. The video compiler will then simply read the choreography file to apply 2D pixel warps. This prevents heavy GPU ML models from breaking the standard CI/CD Github Action. Reference `docs/v2_ml_roadmap.md` for architectural design.