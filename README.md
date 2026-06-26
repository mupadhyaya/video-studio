# Video Studio

Video Studio is an automated pipeline that generates high-quality, dark-mode technical slide presentation videos with AI voiceover narration and a perfectly lip-synced avatar.

## Features (v1 Pipeline)
- **Automated Script to Video:** Takes a structured JSON lesson script and compiles it into a 1080p, 24fps MP4 video.
- **Multilingual Support:** Supports generating both English and Hindi versions (`--lang en` or `--lang hi`).
- **AI Voiceover:** Uses `edge-tts` to dynamically generate clear, natural-sounding voiceovers.
- **Jitter-Free Avatar Lip-Sync:** 
  - Calculates a 6-frame moving average of the audio RMS (volume) to trigger specific mouth visemes (vowel shapes).
  - Uses Computer-Vision template matching (OpenCV) to freeze the avatar's body/shoulders in place and exclusively mask the mouth, preventing any pixel-jitter or drifting.

## Running Locally

1. Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the pipeline on a specific lesson JSON file:
```bash
python run_pipeline.py --input rag_learning_series/lesson_001/lesson_001.json --video-id lesson_001 --lang all
```

## GitHub Actions Workflows

We use automated CI/CD to handle generation without needing local hardware:

*   **Generate Daily Script:** Runs every night at midnight to automatically author new JSON scripts using Google Gemini.
*   **Render On Demand (Re-Render Older Videos):** If you update the avatar assets, fix a bug in the code, or tweak a script, you can re-render older videos directly from GitHub!
    1. Go to the **Actions** tab in the GitHub repository.
    2. Click on the **Render On Demand** workflow on the left side.
    3. Click the **Run workflow** dropdown on the right.
    4. Type the path of the lesson you want to update (e.g., `rag_learning_series/lesson_001/lesson_001.json`).
    5. Hit **Run workflow**. It will automatically compile the new video using the latest code and push the `.mp4` directly back to the `main` branch!

## Architecture Evolution

We enforce strict separation between our stable production pipeline and future ML experimentation.
- **v1 (Current Branch):** Fast, rule-based RMS volume mapping with static, deterministic OpenCV masking. Designed to run quickly and reliably on 2-core GitHub Action CPU runners.
- **v2 (Future Roadmap):** Please see `docs/v2_ml_roadmap.md` for our plans to integrate hyper-optimized, CPU-friendly ONNX/TFLite models to add expressive head-tracking, blinks, and dynamic ML-driven slide layouts.