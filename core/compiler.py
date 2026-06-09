import os
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

def compile_video(slides_data, images_dir, audio_dir, output_path):
    """
    Stitches slide frames and audio clips together into a final 24fps MP4 video.
    Uses MoviePy 2.x method signatures (with_duration, with_audio).
    """
    clips = []
    
    try:
        for i, slide in enumerate(slides_data):
            img_path = os.path.join(images_dir, f"slide_{i}.png")
            audio_path = os.path.join(audio_dir, f"audio_{i}.mp3")
            
            if not os.path.exists(img_path) or not os.path.exists(audio_path):
                raise FileNotFoundError(f"Missing rendering assets for slide index {i}")
            
            # Load audio to measure precise duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Create slide video clip
            slide_clip = ImageClip(img_path).with_duration(duration).with_audio(audio_clip)
            clips.append(slide_clip)
            
        if not clips:
            raise ValueError("No clips were generated to compile.")
            
        # Stitch all slide clips sequentially
        print(f"Stitching {len(clips)} slide clip(s) together...")
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Compile final H.264 encoded video
        print(f"Compiling final H.264 video at 24fps to: {output_path}")
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac"
        )
        
    finally:
        # Guarantee resource cleanup for all loaded clips
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        try:
            final_clip.close()
        except Exception:
            pass
