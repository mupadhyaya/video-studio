import edge_tts

async def generate_speech(text: str, output_path: str, voice: str = "en-US-ChristopherNeural"):
    """
    Renders text to speech using edge-tts asynchronously.
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
