# Video Studio V2: ML-Driven Architecture Roadmap

## 1. Versioning Strategy (v1 vs. v2)
To ensure we do not break the current stable production flow, we will adopt a strict versioning strategy:
- **v1 (Current):** Rule-based, volume-driven lip sync (RMS), static layouts, deterministic OpenCV masking. This remains the default pipeline running daily on GitHub Actions.
- **v2 (Future):** ML-driven choreography. We will create a parallel execution path (e.g., `run_pipeline_v2.py`) or use Git branches (`feature/v2-ml-engine`). 

## 2. GitHub Actions Constraints
GitHub Actions standard runners have **2-core CPUs, 7GB RAM, and no GPUs**. Therefore, our ML models must be hyper-optimized:
- **No Heavy Frameworks:** We will avoid loading massive PyTorch models. Instead, we will export our trained models to **ONNX (Open Neural Network Exchange)** or **TensorFlow Lite**. ONNX runs highly optimized inference on standard CPUs, perfect for GitHub Actions.
- **Pre-computation:** The ML inference will not happen during the video rendering loop. It will run *once* as a pre-processing step to generate a lightweight `choreography.json` file.
- **API Offloading:** For NLP tasks (like summarizing slides or picking keywords), we will use lightweight API calls (like Google Gemini API) rather than running LLMs locally on the runner.

## 3. V2 Pipeline Flow

### Phase A: The ML Director (Pre-processing)
1. **Input:** Takes the raw `lesson.json` script and generated audio.
2. **Audio Analysis (CPU):** A lightweight ONNX model extracts pitch and rhythm to predict head bobbing and blink timestamps.
3. **Content Analysis (API):** A fast API call determines text sentiment and extracts highlight keywords.
4. **Output:** Generates `choreography.json` (timestamped instructions for the avatar and slides).

### Phase B: The Renderer (Unchanged Core)
1. `MoviePy` and `OpenCV` run just like v1.
2. Instead of guessing lip-sync based on raw volume, the compiler reads `choreography.json`.
3. It applies the OpenCV 2D affine warps for head tilts and blinks exactly when the JSON instructs.

## 4. Next Steps for Implementation (When Ready)
1. Create a `v2_experiments/` folder to prototype the ONNX models locally.
2. Keep `core/compiler.py` untouched, but duplicate it as `core/compiler_v2.py` for testing.
3. Write a Python script to convert audio to a JSON choreography array.
