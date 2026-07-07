"""
v3_engine/live_recorder.py

Live Terminal Screen Recorder for V3 pipeline.

This module:
1. Opens a new Terminal window via osascript
2. Runs the lesson's Python code (auto-installing missing deps first)
3. Screen-records the full execution using macOS screencapture
4. Closes the Terminal window automatically after completion
5. Returns the path to the recorded .mov clip
"""

import os
import re
import subprocess
import sys
import time
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Map common import names to pip package names where they differ
IMPORT_TO_PKG = {
    "langchain_core": "langchain-core",
    "langchain_community": "langchain-community",
    "langchain": "langchain",
    "langchain_openai": "langchain-openai",
    "langchain_anthropic": "langchain-anthropic",
    "faiss": "faiss-cpu",
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "bs4": "beautifulsoup4",
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "google.generativeai": "google-generativeai",
}


def _detect_and_install_missing(code: str, python_bin: str, pip_bin: str) -> list[str]:
    """
    Scan code for import statements. Try importing each module.
    If missing, auto-install the corresponding pip package.
    Returns list of packages that were installed.
    """
    # Extract all imported module names
    pattern = re.compile(r"^\s*(?:import|from)\s+([\w\.]+)", re.MULTILINE)
    modules = set(m.split(".")[0] for m in pattern.findall(code))

    installed = []
    for module in modules:
        # Check if module is importable
        check = subprocess.run(
            [python_bin, "-c", f"import {module}"],
            capture_output=True
        )
        if check.returncode != 0:
            # Determine pip package name
            pkg = IMPORT_TO_PKG.get(module, module.replace("_", "-"))
            print(f"  [live_recorder] 📦 Installing missing: {pkg} ...")
            result = subprocess.run(
                [pip_bin, "install", pkg, "-q"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                installed.append(pkg)
            else:
                print(f"  [live_recorder] ⚠️  Could not install {pkg}: {result.stderr[:100]}")

    return installed


def record_code_execution(
    code: str,
    lesson_title: str,
    output_path: str,
    python_bin: str = None,
    pre_run_delay: float = 2.0,
    post_run_delay: float = 3.0,
) -> bool:
    """
    Opens a Terminal window, runs code, and screen-records the execution.
    Auto-installs any missing Python packages before running.
    Terminal window closes automatically after execution.

    Args:
        code: The Python code string to execute.
        lesson_title: Descriptive title shown in terminal window.
        output_path: Absolute path to save the .mov recording.
        python_bin: Python executable to use. Defaults to venv python.
        pre_run_delay: Seconds to pause before typing starts (for camera-ready look).
        post_run_delay: Seconds to keep recording after execution completes.

    Returns:
        True if recording succeeded, False otherwise.
    """
    if python_bin is None:
        python_bin = str(REPO_ROOT / ".venv" / "bin" / "python")

    pip_bin = str(Path(python_bin).parent / "pip3")

    # ── Step 1: Auto-detect and install missing imports ──────────────────
    print(f"  [live_recorder] 🔍 Checking dependencies...")
    missing_packages = _detect_and_install_missing(code, python_bin, pip_bin)
    if missing_packages:
        print(f"  [live_recorder] ✅ Auto-installed: {', '.join(missing_packages)}")

    # ── Step 2: Write code to a temp file ────────────────────────────────
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", prefix="v3_lesson_", delete=False
    ) as f:
        f.write(code)
        temp_script = f.name

    # Estimate recording duration based on code complexity
    line_count = len(code.splitlines())
    estimated_duration = max(12, pre_run_delay + line_count * 0.4 + post_run_delay)

    # ── Step 3: Build shell command ───────────────────────────────────────
    # The terminal will:
    #   - clear screen for a clean look
    #   - print a colored title header
    #   - run the Python script
    #   - print [✓ Done] in green
    #   - wait 4 seconds so the viewer can read the output
    #   - exit (closes the Terminal tab/window automatically)
    safe_title = lesson_title.replace("'", "").replace('"', "")
    shell_cmd = (
        f"clear; "
        f"printf '\\033[1;36m=== {safe_title} ===\\033[0m\\n\\n'; "
        f"{python_bin} {temp_script}; "
        f"printf '\\n\\033[1;32m[✓ Execution complete]\\033[0m\\n'; "
        f"sleep 4; "
        f"exit 0"
    )

    # AppleScript: open a new Terminal window and run the command
    applescript = f"""
tell application "Terminal"
    activate
    set newTab to do script "{shell_cmd}"
    set custom title of newTab to "{safe_title}"
end tell
"""

    print(f"[live_recorder] 🎬 Opening Terminal for: {lesson_title}")
    print(f"[live_recorder] 📄 Script: {temp_script}")
    print(f"[live_recorder] ⏱️  Recording for ~{int(estimated_duration)}s")

    # Launch Terminal via AppleScript
    subprocess.Popen(["osascript", "-e", applescript])

    # Small pause to let Terminal open and become ready
    time.sleep(pre_run_delay)

    # Start screen recording
    recording_duration = int(estimated_duration)
    print(f"[live_recorder] 🔴 Screen recording started -> {output_path}")
    result = subprocess.run(
        ["screencapture", "-V", str(recording_duration), output_path],
        capture_output=True
    )

    # Clean up temp script
    try:
        os.remove(temp_script)
    except Exception:
        pass

    if result.returncode == 0 and Path(output_path).exists():
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"[live_recorder] ✅ Recording saved! ({size_mb:.1f} MB)")
        return True
    else:
        print(f"[live_recorder] ❌ Recording failed: {result.stderr.decode()}")
        return False


def record_with_narration_overlay(
    code: str,
    narration_audio_path: str,
    lesson_title: str,
    output_path: str,
    python_bin: str = None,
) -> bool:
    """
    Records terminal execution and merges it with the narration audio.
    The final video has the real terminal on screen and your cloned voice narrating.
    """
    raw_video = output_path.replace(".mp4", "_raw.mov")

    # Step 1: Record the terminal execution
    success = record_code_execution(
        code=code,
        lesson_title=lesson_title,
        output_path=raw_video,
        python_bin=python_bin,
    )

    if not success:
        return False

    # Step 2: Merge terminal video + narration audio using MoviePy
    try:
        from moviepy import VideoFileClip, AudioFileClip
        video = VideoFileClip(raw_video)
        audio = AudioFileClip(narration_audio_path)

        # Trim/loop audio to match video length
        if audio.duration < video.duration:
            # Pad silence
            from moviepy import concatenate_audioclips
            from moviepy.audio.AudioClip import AudioClip
            silence = AudioClip(
                lambda t: 0, duration=video.duration - audio.duration
            )
            audio = concatenate_audioclips([audio, silence])
        else:
            audio = audio.subclipped(0, video.duration)

        final = video.with_audio(audio)
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
        )
        video.close()
        audio.close()

        # Remove raw recording
        os.remove(raw_video)
        print(f"[live_recorder] ✅ Final video with narration: {output_path}")
        return True

    except Exception as e:
        print(f"[live_recorder] ❌ Merge failed: {e}")
        # Return raw video if merge fails
        import shutil
        shutil.move(raw_video, output_path)
        return True  # still have the raw video


if __name__ == "__main__":
    # Quick smoke test
    test_code = '''
import time

print("=== RAG Pipeline Demo ===")
print()

# Simulate a retrieval step
documents = [
    "RAG stands for Retrieval Augmented Generation",
    "It combines retrieval systems with language models",
    "The retriever finds relevant documents from a corpus",
]

print("Loaded", len(documents), "documents into the knowledge base.")
time.sleep(1)

query = "What is RAG?"
print(f"\\nUser Query: {query}")
print("Retrieving top-3 relevant documents...")
time.sleep(1)

for i, doc in enumerate(documents, 1):
    print(f"  [{i}] {doc}")

print("\\n✅ RAG pipeline complete!")
'''

    success = record_code_execution(
        code=test_code,
        lesson_title="Lesson 12 - RAG Pipeline Demo",
        output_path="/tmp/v3_test_recording.mov",
    )
    print(f"\nTest: {'✅ PASSED' if success else '❌ FAILED'}")
