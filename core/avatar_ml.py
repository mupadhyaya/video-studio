import os
import subprocess
import shutil

def synthesize_talking_face(image_path: str, audio_path: str, output_path: str):
    """
    Synthesize a talking face video using an ML model (e.g., Wav2Lip).
    
    Args:
        image_path (str): Path to the source avatar image (the static face).
        audio_path (str): Path to the audio file containing the speech.
        output_path (str): Path where the synthesized MP4 video should be saved.
        
    Returns:
        bool: True if synthesis succeeded, False otherwise.
    """
    print(f"[ML Avatar] Synthesizing face for {audio_path}")
    
    # Import the newly created runner
    from core.wav2lip_runner import run_inference
    
    env = os.environ.copy()
    venv_bin = os.path.abspath(".venv/bin")
    env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"

    success = run_inference(image_path, audio_path, output_path)
    if success:
        return True
        
    print("[ERROR] ML synthesis placeholder failed or Wav2Lip failed.")
    return False
