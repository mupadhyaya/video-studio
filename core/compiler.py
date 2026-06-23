import os
import math
import numpy as np
from PIL import Image
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, ImageSequenceClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import CrossFadeIn

def compile_video(slides_data, images_dir, audio_dir, output_path):
    clips = []
    
    # Pre-load avatar assets if they exist
    avatars = {}
    expected_avatars = ["idle", "bmp", "ee", "oh", "aa"]
    all_exist = True
    for name in expected_avatars:
        if not os.path.exists(f"assets/avatar_{name}.png"):
            all_exist = False
            break
            
    if all_exist:
        # Determine fixed target size based on 'idle'
        base_img = Image.open("assets/avatar_idle.png")
        aspect = base_img.width / base_img.height
        target_w = int(350 * aspect)
        
        for name in expected_avatars:
            img = Image.open(f"assets/avatar_{name}.png").convert("RGBA")
            # Force exactly the same size for ImageSequenceClip
            avatars[name] = np.array(img.resize((target_w, 350), Image.Resampling.LANCZOS))
        
    try:
        for i, slide in enumerate(slides_data):
            img_base_path = os.path.join(images_dir, f"slide_{i}_base.png")
            img_content_path = os.path.join(images_dir, f"slide_{i}_content.png")
            audio_path = os.path.join(audio_dir, f"audio_{i}.mp3")
            
            if not os.path.exists(img_base_path) or not os.path.exists(img_content_path) or not os.path.exists(audio_path):
                raise FileNotFoundError(f"Missing rendering assets for slide index {i}")
            
            # Load audio to measure precise duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Create composite slide video clip
            base_clip = ImageClip(img_base_path).with_duration(duration)
            
            # Fade in content at 1.5 seconds (or early if duration is short)
            fade_start = min(1.5, duration / 3.0)
            content_duration = max(0.1, duration - fade_start)
            
            content_clip = (ImageClip(img_content_path)
                            .with_start(fade_start)
                            .with_duration(content_duration)
                            .with_effects([CrossFadeIn(1.0)]))
                            
            # [USER REQUEST: Avatar overlay temporarily disabled for later fixing]
            # if avatars:
            #     ...
            slide_clip = CompositeVideoClip([base_clip, content_clip]).with_duration(duration).with_audio(audio_clip)

            clips.append(slide_clip)
            
        if not clips:
            raise ValueError("No clips were generated to compile.")
            
        # Stitch all slide clips sequentially
        print(f"Stitching {len(clips)} slide clip(s) together with crossfade and synchronized reveal...")
        
        transition_clips = []
        for i, clip in enumerate(clips):
            if i > 0:
                transition_clips.append(clip.with_effects([CrossFadeIn(1.0)]))
            else:
                transition_clips.append(clip)
            
        final_clip = concatenate_videoclips(transition_clips, padding=-1.0, method="compose")
        
        # Compile final H.264 encoded video
        print(f"Compiling final H.264 video at 24fps to: {output_path}")
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            pixel_format="yuv420p"
        )
        
    finally:
        for clip in clips:
            try: clip.close()
            except: pass
        try: final_clip.close()
        except: pass
