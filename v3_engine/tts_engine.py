"""
v3_engine/tts_engine.py

Text-to-speech engine for V3 pipeline.

Strategy (in priority order):
  1. F5-TTS (local voice cloning with your voice) — best quality, requires model download
  2. edge-tts (Microsoft cloud TTS) — good quality, needs internet, used as fallback
  3. gtts (Google TTS) — last resort

Usage:
    from v3_engine.tts_engine import synthesize
    synthesize("Hello world", "output.mp3", lang="en")
"""

import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REFERENCE_VOICE = REPO_ROOT / "assets" / "my_voice.wav"

# Voice map per language for edge-tts
EDGE_VOICES = {
    "en": "en-IN-PrabhatNeural",   # Indian English male
    "hi": "hi-IN-MadhurNeural",    # Hindi male
}


def synthesize(text: str, output_path: str, lang: str = "en") -> bool:
    """
    Synthesize speech for the given text. Tries best available engine.

    Args:
        text: Narration text.
        output_path: Output .wav or .mp3 file path.
        lang: "en" or "hi".

    Returns:
        True if audio was written to output_path.
    """
    if not text or not text.strip():
        return False

    # Try F5-TTS first (your cloned voice)
    if REFERENCE_VOICE.exists():
        ok = _try_f5tts(text, output_path, lang)
        if ok:
            return True

    # Fallback to edge-tts
    ok = _try_edge_tts(text, output_path, lang)
    if ok:
        return True

    # Last resort: gtts
    return _try_gtts(text, output_path, lang)


def _try_f5tts(text: str, output_path: str, lang: str) -> bool:
    """Attempt F5-TTS voice cloning. Fails gracefully if model not downloaded."""
    try:
        from f5_tts.api import F5TTS
        ref_text = (
            "Hello, I am Mohit Upadhyaya and welcome to this lesson on "
            "machine learning and artificial intelligence concepts."
        )
        model = F5TTS()
        wav, sr, _ = model.infer(
            ref_file=str(REFERENCE_VOICE),
            ref_text=ref_text,
            gen_text=text,
            show_info=False,
        )
        import soundfile as sf
        sf.write(output_path, wav, sr)
        print(f"  [tts] ✅ F5-TTS cloned voice → {Path(output_path).name}")
        return Path(output_path).exists()
    except Exception as e:
        if "No such file" in str(e) or "model" in str(e).lower() or "download" in str(e).lower():
            print(f"  [tts] ⚠️  F5-TTS model not yet downloaded. Falling back to edge-tts.")
        else:
            print(f"  [tts] ⚠️  F5-TTS failed ({e}). Falling back to edge-tts.")
        return False


def _try_edge_tts(text: str, output_path: str, lang: str) -> bool:
    """Use Microsoft edge-tts for narration."""
    try:
        import edge_tts

        voice = EDGE_VOICES.get(lang, EDGE_VOICES["en"])

        async def _synth():
            # edge-tts saves as mp3 natively
            mp3_path = output_path.replace(".wav", ".mp3")
            if not mp3_path.endswith(".mp3"):
                mp3_path = output_path + ".mp3"

            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(mp3_path)

            # Convert mp3 → wav for MoviePy compatibility
            if output_path.endswith(".wav"):
                from moviepy import AudioFileClip
                clip = AudioFileClip(mp3_path)
                clip.write_audiofile(output_path, fps=22050, logger=None)
                clip.close()
                os.remove(mp3_path)
            else:
                # Keep as mp3
                import shutil
                shutil.move(mp3_path, output_path)

        asyncio.run(_synth())
        exists = Path(output_path).exists()
        if exists:
            print(f"  [tts] ✅ edge-tts ({voice}) → {Path(output_path).name}")
        return exists

    except Exception as e:
        print(f"  [tts] ⚠️  edge-tts failed: {e}")
        return False


def _try_gtts(text: str, output_path: str, lang: str) -> bool:
    """Last resort: Google TTS via gtts."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="hi" if lang == "hi" else "en", slow=False)
        mp3_path = output_path.replace(".wav", ".mp3")
        tts.save(mp3_path)
        if output_path.endswith(".wav"):
            from moviepy import AudioFileClip
            clip = AudioFileClip(mp3_path)
            clip.write_audiofile(output_path, fps=22050, logger=None)
            clip.close()
            os.remove(mp3_path)
        print(f"  [tts] ✅ gtts fallback → {Path(output_path).name}")
        return Path(output_path).exists()
    except Exception as e:
        print(f"  [tts] ❌ gtts also failed: {e}")
        return False


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Welcome to Understanding AIML. Today we build a RAG pipeline."
    lang = sys.argv[2] if len(sys.argv) > 2 else "en"
    out = "/tmp/v3_tts_test.mp3"
    ok = synthesize(text, out, lang=lang)
    print(f"Result: {'✅' if ok else '❌'} → {out}")
