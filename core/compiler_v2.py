import os
import math
import numpy as np
from PIL import Image
from moviepy import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips, ImageSequenceClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import CrossFadeIn
from core.avatar_ml import synthesize_talking_face

def compile_video(slides_data, images_dir, audio_dir, output_path):
    clips = []
    
    is_hindi = output_path.endswith("_hi.mp4")
    
    # 1. Select the base idle avatar image
    if is_hindi:
        avatar_idle_path = "assets/masked_hindi_rest.png"
    else:
        avatar_idle_path = "assets/masked_avatar_0.png"
        
    has_avatar = os.path.exists(avatar_idle_path)
    if not has_avatar:
        print(f"Warning: Missing {avatar_idle_path} in assets/. ML Avatar overlay disabled.")
        
    global_time_offset = 0.0
        
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
                            
            composite_layers = [base_clip, content_clip]
            
            # --- 2. ML Lip-sync Generation ---
            if has_avatar:
                print(f"  Generating ML synchronized lip-sync for slide {i}...")
                
                # We will synthesize the face into a temporary video file
                temp_avatar_video = os.path.join(images_dir, f"slide_{i}_ml_avatar.mp4")
                
                success = synthesize_talking_face(avatar_idle_path, audio_path, temp_avatar_video)
                
                if success and os.path.exists(temp_avatar_video):
                    # Load the generated talking head video
                    avatar_video_clip = VideoFileClip(temp_avatar_video)
                    
                    # Ensure it matches slide duration
                    if abs(avatar_video_clip.duration - duration) > 0.1:
                        avatar_video_clip = avatar_video_clip.with_duration(duration)
                        
                    # Calculate target width while maintaining aspect ratio, target height 350px
                    vw, vh = base_clip.size
                    
                    # Read size from original image to get proper aspect ratio
                    with Image.open(avatar_idle_path) as img:
                        aspect = img.width / img.height
                        target_w = int(350 * aspect)
                        
                    # Resize the video clip
                    avatar_video_clip = avatar_video_clip.resized(height=350)
                    
                    # Apply original alpha mask to remove black background
                    avatar_mask = ImageClip(avatar_idle_path).resized(height=350).mask
                    avatar_video_clip = avatar_video_clip.with_mask(avatar_mask)
                    
                    # Position at bottom right
                    ax = vw - target_w - 40
                    ay = vh - 350 - 40
                    
                    # Apply breathing animation (scale slightly over a 2-second loop)
                    # We use moviepy's resize with a custom function of time
                    def breathing_scale(t):
                        # Sinusoidal scaling between 1.0 and 1.03 over 3 seconds
                        return 1.0 + 0.015 * (1 + math.sin(2 * math.pi * t / 3.0))
                    
                    # Store original mask so we can restore it after resize
                    avatar_video_clip = avatar_video_clip.with_position((ax, ay)).without_audio()
                    
                    def make_breathing(offset, base_x, base_y):
                        def breathing_position(t):
                            dy = 8 * math.sin(2 * math.pi * (t + offset) / 3.0)
                            return (base_x, base_y + dy)
                        return breathing_position
                        
                    avatar_video_clip = avatar_video_clip.with_position(make_breathing(global_time_offset, ax, ay))
                    
                    composite_layers.append(avatar_video_clip)
                else:
                    print(f"Warning: ML avatar synthesis failed for slide {i}. Falling back to static breathing avatar.")
                    
                    # Read size from original image to get proper aspect ratio
                    with Image.open(avatar_idle_path) as img:
                        aspect = img.width / img.height
                        target_w = int(350 * aspect)
                        
                    vw, vh = base_clip.size
                    ax = vw - target_w - 40
                    ay = vh - 350 - 40
                    
                    fallback_clip = (ImageClip(avatar_idle_path)
                                     .resized(height=350)
                                     .with_duration(duration))
                    
                    def make_breathing(offset, base_x, base_y):
                        def breathing_position(t):
                            dy = 8 * math.sin(2 * math.pi * (t + offset) / 3.0)
                            return (base_x, base_y + dy)
                        return breathing_position
                        
                    fallback_clip = fallback_clip.with_position(make_breathing(global_time_offset, ax, ay))
                    composite_layers.append(fallback_clip)
            
            global_time_offset += duration
            
            slide_clip = CompositeVideoClip(composite_layers).with_duration(duration).with_audio(audio_clip)

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
            pixel_format="yuv420p",
            bitrate="12000k",
            preset="slow",
            threads=4
        )
        
    finally:
        for clip in clips:
            try: clip.close()
            except: pass
        try: final_clip.close()
        except: pass
