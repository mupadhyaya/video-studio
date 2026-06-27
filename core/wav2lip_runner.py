import os
import subprocess
import urllib.request
import sys

WAV2LIP_DIR = os.path.abspath("Wav2Lip")
WAV2LIP_REPO = "https://github.com/Rudrabha/Wav2Lip.git"

# Using a public HuggingFace mirror for the weights to avoid Google Drive download limits
WAV2LIP_GAN_URL = "https://huggingface.co/camenduru/Wav2Lip/resolve/main/checkpoints/wav2lip_gan.pth"
S3FD_URL = "https://huggingface.co/camenduru/Wav2Lip/resolve/main/face_detection/detection/sfd/s3fd.pth"

def download_file(url, dest):
    if not os.path.exists(dest):
        print(f"Downloading {url} to {dest}...")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            subprocess.run(["curl", "--retry", "5", "--retry-all-errors", "-L", "-o", dest, url], check=True)
            print("Download complete.")
        except subprocess.CalledProcessError:
            print(f"Failed to download {url}")
            if os.path.exists(dest):
                os.remove(dest)
            sys.exit(1)
    else:
        print(f"File {dest} already exists.")

def setup_wav2lip():
    """Clones the Wav2Lip repo and downloads required weights if they don't exist."""
    if not os.path.exists(os.path.join(WAV2LIP_DIR, "inference.py")):
        print(f"Cloning Wav2Lip repository into {WAV2LIP_DIR}...")
        if not os.path.exists(WAV2LIP_DIR):
            os.makedirs(WAV2LIP_DIR)
        subprocess.run(["git", "init"], cwd=WAV2LIP_DIR, check=True)
        subprocess.run(["git", "remote", "add", "origin", WAV2LIP_REPO], cwd=WAV2LIP_DIR, check=False)
        subprocess.run(["git", "fetch", "origin", "master"], cwd=WAV2LIP_DIR, check=True)
        subprocess.run(["git", "reset", "--hard", "FETCH_HEAD"], cwd=WAV2LIP_DIR, check=True)
    
    # Download main GAN weights
    checkpoints_dir = os.path.join(WAV2LIP_DIR, "checkpoints")
    gan_weights_path = os.path.join(checkpoints_dir, "wav2lip_gan.pth")
    download_file(WAV2LIP_GAN_URL, gan_weights_path)
    
    # Download face detection weights
    face_det_dir = os.path.join(WAV2LIP_DIR, "face_detection", "detection", "sfd")
    s3fd_weights_path = os.path.join(face_det_dir, "s3fd.pth")
    download_file(S3FD_URL, s3fd_weights_path)

def run_inference(image_path, audio_path, output_path):
    """Runs the Wav2Lip inference script."""
    print(f"Running Wav2Lip inference on {image_path} and {audio_path}...")
    
    setup_wav2lip()
    
    inference_script = os.path.join(WAV2LIP_DIR, "inference.py")
    checkpoint_path = os.path.join(WAV2LIP_DIR, "checkpoints", "wav2lip_gan.pth")
    
    # Run the inference script in the Wav2Lip directory context
    cmd = [
        sys.executable, inference_script,
        "--checkpoint_path", checkpoint_path,
        "--face", os.path.abspath(image_path),
        "--audio", os.path.abspath(audio_path),
        "--outfile", os.path.abspath(output_path),
        "--pads", "0", "10", "0", "0" # slight padding to avoid cropping the chin
    ]
    # Create environment with .venv/bin for ffmpeg
    env = os.environ.copy()
    venv_bin = os.path.abspath(".venv/bin")
    env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"

    try:
        subprocess.run(cmd, cwd=WAV2LIP_DIR, check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Wav2Lip inference failed: {e}")
        return False

if __name__ == "__main__":
    # Test script setup
    setup_wav2lip()
