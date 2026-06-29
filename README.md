# Video Studio

Video Studio is an automated pipeline that generates high-quality, dark-mode technical slide presentation videos with AI voiceover narration and a perfectly lip-synced avatar.

## Features (v2 Pipeline - *New!*)
- **True ML Lip-Syncing:** Upgraded from the v1 rule-based viseme system to a full **Wav2Lip** implementation for pixel-perfect lip synchronization matching the TTS audio.
- **Dynamic Avatar Realism:** Features a custom mathematical engine within MoviePy that applies a subtle "breathing" and head-bobbing scale animation to the avatar, bypassing the need for GPU-heavy models like LivePortrait.
- **Transparent Masking Pipeline:** Retains the crisp Alpha Channel transparency behind the ML avatar, ensuring the avatar flawlessly overlays onto dark-mode slides without black backgrounds.
- **Dual-Language Generation:** Seamlessly generates localized scripts and renders videos in both English and Hindi, complete with gender-accurate localized narration.
- **Robust ML Fallback Mechanism:** Automatically detects Wav2Lip build errors and gracefully switches to a continuous, high-quality "breathing" fallback avatar, ensuring daily automated CI/CD runs never fail catastrophically.
- **Auto YouTube Thumbnails:** Automatically extracts the Title Slide and renders a beautiful HD 1280x720 YouTube thumbnail utilizing Lanczos upscaling for ultimate clarity.
- **Practical RAG Curriculum:** Integrated Gemini prompts enforce generating hands-on, highly accurate Python code exercises on the slides, interleaving theory with project-based execution.

## Running Locally

1. Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements_v2.txt
```

2. Run the pipeline on a specific lesson JSON file:
```bash
python run_pipeline_v2.py --input rag_learning_series/lesson_001/lesson_001.json --video-id lesson_001 --lang all
```

## GitHub Actions Workflows (v2 Optimized)

We use automated CI/CD to handle generation without needing local hardware. 
**Note:** Our v2 ML pipeline leverages `actions/cache@v3` to instantaneously retrieve the 400MB Wav2Lip models securely on the runner, bypassing download wait times!

*   **V2 Daily Render:** Runs every night at midnight to automatically author new JSON scripts using Google Gemini and render them via the v2 pipeline.
*   **V2 Render On Demand (Re-Render Older Videos):** If you update the avatar assets, fix a bug in the code, or tweak a script, you can re-render older videos directly from GitHub!
    1. Go to the **Actions** tab in the GitHub repository.
    2. Click on the **V2 Render On Demand** workflow on the left side.
    3. Click the **Run workflow** dropdown on the right.
    4. Type the path of the lesson you want to update (e.g., `rag_learning_series/lesson_001/lesson_001.json`).
    5. Hit **Run workflow**. It will automatically compile the new video using the latest Wav2Lip engine and push the `.mp4` and `.png` thumbnail directly back to the `main` branch!

## Legacy Support (v1)

We enforce strict separation between our stable production pipelines. The original v1 pipeline (using deterministic OpenCV viseme mapping) is fully retained and can be run via `run_pipeline.py`.