import os
import math
import numpy as np
from PIL import Image
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, ImageSequenceClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import CrossFadeIn

def compile_video(slides_data, images_dir, audio_dir, output_path):
    clips = []
    
    # 1. Avatar Pre-loading
    avatars = {}
    
    is_hindi = output_path.endswith("_hi.mp4")
    
    if is_hindi:
        # HINDI LOGIC: Use perfectly stable masked avatars
        viseme_mapping_hi = [
            "hindi_rest",
            "hindi_bmp",
            "hindi_aa",
            "hindi_oh",
            "hindi_ee",
            "hindi_ai"
        ]
        
        all_exist = True
        for name in viseme_mapping_hi:
            if not os.path.exists(f"assets/masked_{name}.png"):
                all_exist = False
                break
                
        if all_exist:
            print("Loading OpenCV mouth-masked HINDI avatar images for zero facial jitter...")
            base_img = Image.open("assets/masked_hindi_rest.png")
            aspect = base_img.width / base_img.height
            target_w = int(350 * aspect)
            
            for name in viseme_mapping_hi:
                img = Image.open(f"assets/masked_{name}.png").convert("RGBA")
                resized = img.resize((target_w, 350), Image.Resampling.LANCZOS)
                avatars[name] = np.array(resized)
        else:
            print("Warning: Missing masked_hindi_X.png in assets/. Hindi Avatar overlay disabled.")
    else:
        # ENGLISH LOGIC: OpenCV Masked Avatars (from previous step)
        viseme_mapping = {
            "idle": 0,
            "bmp":  0,
            "ee":   1,
            "fv":   1,
            "oh":   2,
            "aa":   3
        }
        
        all_exist = True
        for i in range(4):
            if not os.path.exists(f"assets/masked_avatar_{i}.png"):
                all_exist = False
                break
                
        if all_exist:
            print("Loading OpenCV mouth-masked avatar images for zero facial jitter (English)...")
            base_img = Image.open("assets/masked_avatar_0.png")
            aspect = base_img.width / base_img.height
            target_w = int(350 * aspect)
            
            for name, file_idx in viseme_mapping.items():
                img = Image.open(f"assets/masked_avatar_{file_idx}.png").convert("RGBA")
                resized = img.resize((target_w, 350), Image.Resampling.LANCZOS)
                avatars[name] = np.array(resized)
        else:
            print("Warning: Missing masked_avatar_X.png in assets/. Avatar overlay disabled.")
        
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
                
                total_frames = int(duration * fps)
                avatar_frames = []
                
                # 1. Calculate raw RMS per frame
                raw_rms = []
                for f_idx in range(total_frames):
                    start_sample = f_idx * samples_per_video_frame
                    end_sample = min(start_sample + samples_per_video_frame, len(audio_array))
                    
                    if start_sample >= len(audio_array):
                        raw_rms.append(0.0)
                    else:
                        chunk = audio_array[start_sample:end_sample]
                        if len(chunk) > 0:
                            raw_rms.append(np.sqrt(np.mean(chunk**2)))
                        else:
                            raw_rms.append(0.0)
                
                # 2. Smooth the volume data to remove rapid flapping/jitter
                # A 6-frame window (250ms) is perfect to blend out micro-bursts and smooth Hindi lip-sync
                window_size = 6 if is_hindi else 4
                if len(raw_rms) >= window_size:
                    smoothed_rms = np.convolve(raw_rms, np.ones(window_size)/window_size, mode='same')
                else:
                    smoothed_rms = raw_rms
                    
                # 3. Assign visemes based on smoothed RMS
                for rms in smoothed_rms:
                    if is_hindi:
                        # HINDI OPTIMIZED THRESHOLDS
                        if rms < 0.05:
                            viseme = "hindi_rest"
                        elif rms < 0.12:
                            viseme = "hindi_ai"
                        elif rms < 0.20:
                            viseme = "hindi_ee"
                        elif rms < 0.30:
                            viseme = "hindi_oh"
                        elif rms < 0.40:
                            viseme = "hindi_bmp"
                        else:
                            viseme = "hindi_aa"
                    else:
                        # ENGLISH STANDARD THRESHOLDS
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
                vw, vh = base_clip.size
                ax = vw - target_w - 40
                ay = vh - 350 - 40
                avatar_clip = ImageSequenceClip(avatar_frames, fps=fps).with_position((ax, ay)).with_duration(duration)
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
