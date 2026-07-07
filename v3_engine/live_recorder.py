"""
v3_engine/live_recorder.py

Live Terminal Screen Recorder for V3 pipeline.

This module:
1. Opens a new Terminal window via osascript
2. Types and runs the lesson's Python code
3. Screen-records the execution using macOS screencapture
4. Returns the path to the recorded .mov clip

The recording is a real, authentic terminal execution — no faking.
"""

import os
import subprocess
import time
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


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

    Args:
        code: The Python code string to execute.
        lesson_title: Descriptive title shown in terminal window.
        output_path: Path to save the .mov recording.
        python_bin: Python executable to use. Defaults to venv python.
        pre_run_delay: Seconds to pause before typing starts (for camera-ready look).
        post_run_delay: Seconds to keep recording after execution completes.

    Returns:
        True if recording succeeded, False otherwise.
    """
    if python_bin is None:
        python_bin = str(REPO_ROOT / ".venv" / "bin" / "python")

    # Write code to a temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", prefix="v3_lesson_", delete=False
    ) as f:
        f.write(code)
        temp_script = f.name

    # Estimate execution time to size the recording
    line_count = len(code.splitlines())
    estimated_duration = max(10, pre_run_delay + line_count * 0.5 + post_run_delay)

    # AppleScript to open Terminal, set title, and run the script
    applescript = f"""
tell application "Terminal"
    activate
    set newTab to do script "clear && echo '=== {lesson_title} ===' && echo '' && {python_bin} {temp_script}; echo ''; echo '[Done. Press Ctrl-C to close]'"
    set custom title of newTab to "{lesson_title}"
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
