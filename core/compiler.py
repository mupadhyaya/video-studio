import os
import math
import numpy as np
from PIL import Image
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, ImageSequenceClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import CrossFadeIn

def compile_video(slides_data, images_dir, audio_dir, output_path):
    clips = []
    
    # 1. Avatar Grid Processing
    avatars = {}
    master_grid_path = "assets/MASTER_AVATAR_6VISEME_GRID.png"
    if os.path.exists(master_grid_path):
        print("Loading and slicing master avatar grid...")
        img = Image.open(master_grid_path).convert("RGBA")
        frame_w = img.width // 3
        frame_h = img.height // 2
        
        # Mapping: Row 1: idle, bmp, aa. Row 2: oh, ee, fv
        viseme_names = ["idle", "bmp", "aa", "oh", "ee", "fv"]
        
        # Calculate target dimensions: height 350px
        aspect = frame_w / frame_h
        target_w = int(350 * aspect)
        
        for idx, name in enumerate(viseme_names):
            row = idx // 3
            col = idx % 3
            left = col * frame_w
            upper = row * frame_h
            right = left + frame_w
            lower = upper + frame_h
            
            # Crop the grid
            cropped = img.crop((left, upper, right, lower))
            
            # Resize
            resized = cropped.resize((target_w, 350), Image.Resampling.LANCZOS)
            avatars[name] = np.array(resized)
    else:
        print("Warning: MASTER_AVATAR_6VISEME_GRID.png not found. Avatar overlay will be disabled.")
        
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
            
            # --- 2. Audio RMS Processing & Lip-sync ---
            if avatars:
                print(f"  Generating synchronized lip-sync for slide {i}...")
                fps = 24
                
                try:
                    audio_array = audio_clip.to_soundarray()
                except Exception as e:
                    print(f"Error reading audio array: {e}")
                    audio_array = np.zeros((int(duration * audio_clip.fps), 2))
                
                audio_fps = audio_clip.fps
                samples_per_video_frame = int(audio_fps / fps)
                
                avatar_frames = []
                total_frames = int(duration * fps)
                
                for f_idx in range(total_frames):
                    start_sample = f_idx * samples_per_video_frame
                    end_sample = min(start_sample + samples_per_video_frame, len(audio_array))
                    
                    if start_sample >= len(audio_array):
                        rms = 0.0
                    else:
                        chunk = audio_array[start_sample:end_sample]
                        if len(chunk) > 0:
                            # RMS = sqrt(mean(chunk^2))
                            rms = np.sqrt(np.mean(chunk**2))
                        else:
                            rms = 0.0
                    
                    # 3. Tiered Volume-Banded Mapping
                    if rms < 0.05:
                        viseme = "idle"
                    elif rms < 0.12:
                        viseme = "ee"
                    elif rms < 0.20:
                        viseme = "fv"
                    elif rms < 0.30:
                        viseme = "oh"
                    else:
                        viseme = "aa"
                        
                    avatar_frames.append(avatars[viseme])
                
                # 4. Video Compositing
                avatar_clip = ImageSequenceClip(avatar_frames, fps=fps).with_position(("right", "bottom")).with_duration(duration)
                composite_layers.append(avatar_clip)
                
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
            pixel_format="yuv420p"
        )
        
    finally:
        for clip in clips:
            try: clip.close()
            except: pass
        try: final_clip.close()
        except: pass
