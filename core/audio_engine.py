import edge_tts
from gtts import gTTS

# Voice model mapping by language code
EDGE_TTS_VOICES = {
    "en": "en-US-JennyNeural",
    "hi": "hi-IN-SwaraNeural",
}

# gTTS fallback configuration by language code
GTTS_CONFIG = {
    "en": {"lang": "en", "tld": "com"},
    "hi": {"lang": "hi", "tld": "co.in"},
}


async def generate_speech(text: str, output_path: str, lang_code: str = "en"):
    """
    Renders text to speech using edge-tts asynchronously.
    Falls back to gTTS (synchronous) if edge-tts fails.

    Args:
        text: The narration text to synthesize.
        output_path: File path for the output MP3.
        lang_code: Language code — "en" for English, "hi" for Hindi.
    """
    voice = EDGE_TTS_VOICES.get(lang_code, EDGE_TTS_VOICES["en"])

    try:
        # Slow down the narration rate by 15% for a more lecture-like pace
        communicate = edge_tts.Communicate(text, voice, rate="-15%")
        await communicate.save(output_path)
    except Exception as e:
        print(f"  [WARN] edge-tts failed ({e}), falling back to gTTS...")
        config = GTTS_CONFIG.get(lang_code, GTTS_CONFIG["en"])
        tts = gTTS(text=text, lang=config["lang"], tld=config["tld"])
        tts.save(output_path)
