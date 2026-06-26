import math
import os
from moviepy.editor import ImageClip

def generate_breathing_video(image_path, output_path, duration=3.0):
    print(f"Generating synthetic breathing video from {image_path}...")
    
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return

    # Load image with alpha channel
    clip = ImageClip(image_path).with_duration(duration)
    
    # Apply a subtle breathing effect (scale up and down by 2%)
    def breathing_scale(t):
        # Sinusoidal scaling between 1.0 and 1.02 over the duration
        return 1.0 + 0.02 * (1 + math.sin(2 * math.pi * t / (duration / 2)))
        
    def breathing_position(t):
        # Bob up and down by a few pixels
        dy = 15 * math.sin(2 * math.pi * t / duration)
        return ("center", "center") # Actually moviepy handles position better when composited, but for resize it scales from center

    # Resize over time
    animated_clip = clip.resize(breathing_scale)
    
    print(f"Saving to {output_path}...")
    # Export as WebM with alpha channel to preserve transparency
    animated_clip.write_videofile(
        output_path,
        fps=24,
        codec="libvpx-vp9",
        ffmpeg_params=["-pix_fmt", "yuva420p"]
    )
    print("Done!")

if __name__ == "__main__":
    os.makedirs("assets/animations", exist_ok=True)
    generate_breathing_video("assets/masked_avatar_0.png", "assets/animations/idle_avatar_en.webm")
    generate_breathing_video("assets/masked_hindi_rest.png", "assets/animations/idle_avatar_hi.webm")
