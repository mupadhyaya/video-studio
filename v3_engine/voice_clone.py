"""
v3_engine/voice_clone.py

Local voice cloning using F5-TTS.
Uses assets/my_voice.wav as the reference voice to synthesize any text
in the user's vocal style — no API keys required.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REFERENCE_VOICE = REPO_ROOT / "assets" / "my_voice.wav"
REFERENCE_VOICE_TEXT = "Hello, I am Mohit Upadhyaya and welcome to this lesson on machine learning and AI concepts."


def synthesize_speech(text: str, output_path: str) -> bool:
    """
    Synthesize speech in the user's cloned voice using F5-TTS CLI.

    Args:
        text: The narration text to synthesize.
        output_path: Absolute path to save the output .wav file.

    Returns:
        True if synthesis succeeded, False otherwise.
    """
    if not REFERENCE_VOICE.exists():
        print(f"[voice_clone] ERROR: Reference voice not found at {REFERENCE_VOICE}")
        return False

    print(f"[voice_clone] Synthesizing: '{text[:60]}...'")

    python = sys.executable
    cmd = [
        python, "-m", "f5_tts.infer.infer_cli",
        "--model", "F5TTS_v1_Base",
        "--ref_audio", str(REFERENCE_VOICE),
        "--ref_text", REFERENCE_VOICE_TEXT,
        "--gen_text", text,
        "--output_file", output_path,
        "--vocoder_name", "vocos",
        "--load_vocoder_from_local",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"[voice_clone] ✅ Saved to {output_path}")
            return True
        else:
            print(f"[voice_clone] ❌ F5-TTS failed:\n{result.stderr}")
            # Fallback to edge-tts if F5-TTS fails
            return _fallback_edge_tts(text, output_path)
    except subprocess.TimeoutExpired:
        print("[voice_clone] ❌ Synthesis timed out. Falling back to edge-tts.")
        return _fallback_edge_tts(text, output_path)
    except Exception as e:
        print(f"[voice_clone] ❌ Exception: {e}. Falling back to edge-tts.")
        return _fallback_edge_tts(text, output_path)


def _fallback_edge_tts(text: str, output_path: str) -> bool:
    """Fallback to edge-tts if local voice cloning fails."""
    import asyncio
    try:
        import edge_tts
    except ImportError:
        print("[voice_clone] edge-tts not available either.")
        return False

    async def _synth():
        communicate = edge_tts.Communicate(text, "en-IN-NeerjaNeural")
        # edge-tts outputs mp3, convert path
        mp3_path = output_path.replace(".wav", ".mp3")
        await communicate.save(mp3_path)
        # Convert mp3 to wav using moviepy
        from moviepy import AudioFileClip
        clip = AudioFileClip(mp3_path)
        clip.write_audiofile(output_path, fps=22050)
        clip.close()
        os.remove(mp3_path)

    try:
        asyncio.run(_synth())
        return Path(output_path).exists()
    except Exception as e:
        print(f"[voice_clone] Fallback also failed: {e}")
        return False


if __name__ == "__main__":
    # Quick test
    out = "/tmp/test_voice_clone.wav"
    success = synthesize_speech(
        "Welcome to Lesson 12 on Retrieval Augmented Generation. "
        "Today we will build a complete RAG pipeline from scratch.",
        out
    )
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")
    if success:
        print(f"Output: {out}")
