import os
import sys
import json
import argparse
from moviepy import VideoFileClip, TextClip, ColorClip, CompositeVideoClip

def generate_short(json_path, video_path, lang="en"):
    print(f"🎬 Generating YouTube Short for {video_path}...")
    
    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        
    lesson_data = raw_data.get("storyboard", raw_data)
    
    # 1. Calculate timestamps for all slides to find the "best" hook slide
    audio_dir = os.path.abspath(f"temp_build_{lang}")
    current_time = 0.0
    best_slide_idx = -1
    best_slide_score = -1
    best_start = 0.0
    best_end = 0.0
    
    if not os.path.exists(audio_dir):
        print(f"Warning: audio dir {audio_dir} not found. Using default timestamps (0s to 10s).")
        best_slide_idx = 0
        best_start = 0.0
        best_end = min(10.0, VideoFileClip(video_path).duration)
    else:
        from moviepy import AudioFileClip
        for i, slide in enumerate(lesson_data):
            audio_path = os.path.join(audio_dir, f"audio_{i}.mp3")
            start_time = current_time
            duration = 5.0
            
            if os.path.exists(audio_path):
                with AudioFileClip(audio_path) as audio_clip:
                    duration = audio_clip.duration
                    
            end_time = start_time + duration
            
            # Scoring logic to find the most "viral" or engaging slide
            score = 0
            v_type = slide.get("visual_type", "")
            if v_type == "architecture_diagram":
                score += 100
            elif v_type == "sequence_diagram":
                score += 90
            elif v_type == "code_snippet":
                score += 80
            elif v_type == "terminal_output":
                score += 70
            else:
                score += duration # Longer conceptual slides get higher score
                
            if score > best_slide_score:
                best_slide_score = score
                best_slide_idx = i
                best_start = start_time
                best_end = end_time
                
            current_time = end_time
            
        if best_slide_idx == -1:
            print("Could not determine a slide for the short.")
            return
        
    print(f"🎯 Selected Slide {best_slide_idx + 1} ({lesson_data[best_slide_idx].get('visual_type')}) for the Short.")
    print(f"✂️ Slicing video from {best_start:.2f}s to {best_end:.2f}s...")
    
    # Ensure the short is less than 60 seconds
    if (best_end - best_start) > 59.0:
        best_end = best_start + 59.0
        
    try:
        with VideoFileClip(video_path) as main_video:
            highlight = main_video.subclipped(best_start, best_end)
            
            from PIL import Image, ImageFilter
            import numpy as np
            
            def blur_frame(image):
                img = Image.fromarray(image)
                return np.array(img.filter(ImageFilter.GaussianBlur(30)))
            
            # The original main_video is 1920x1080 (16:9). We want to scale it to height 1920 to fill the background, then blur it.
            bg_video = (highlight
                        .resized(height=1920)
                        .cropped(x_center=highlight.resized(height=1920).size[0]/2, width=1080)
                        .image_transform(blur_frame)
                        .with_duration(highlight.duration))
            
            # Dim the background a bit for better text contrast
            dark_overlay = ColorClip(size=(1080, 1920), color=(0, 0, 0)).with_opacity(0.4).with_duration(highlight.duration)
            
            # Main video centered
            resized_highlight = highlight.resized(width=1080)
            video_y_pos = (1920 - resized_highlight.size[1]) / 2
            positioned_video = resized_highlight.with_position(('center', video_y_pos))
            
            # Dynamic Header
            lesson_title = raw_data.get("meta_title", "Concept Highlight")
            header_text = TextClip(text=lesson_title, font_size=70, color='white', method='caption', size=(900, None), horizontal_align='center')
            header = header_text.with_position(('center', 250)).with_duration(highlight.duration)
            
            # Subheader
            slide_title = lesson_data[best_slide_idx].get(f"title_{lang}", lesson_data[best_slide_idx].get("title", ""))
            subheader_text = TextClip(text=slide_title, font_size=50, color='#00FFCC', method='caption', size=(900, None), horizontal_align='center')
            subheader = subheader_text.with_position(('center', 450)).with_duration(highlight.duration)
            
            # Footer CTA
            cta_text = TextClip(text="👇 Full Tutorial Link in Description 👇", font_size=55, color='yellow', method='caption', size=(900, None), horizontal_align='center')
            cta = cta_text.with_position(('center', 1550)).with_duration(highlight.duration)
            
            final = CompositeVideoClip([bg_video, dark_overlay, positioned_video, header, subheader, cta])
            
            out_path = video_path.replace(".mp4", "_short.mp4")
            
            print(f"🎬 Rendering Short: {out_path}")
            final.write_videofile(
                out_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",
                logger=None
            )
            print(f"✅ Successfully created YouTube Short!")
            
    except Exception as e:
        print(f"❌ Failed to generate short: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Path to lesson JSON")
    parser.add_argument("--video", required=True, help="Path to full MP4 video")
    parser.add_argument("--lang", default="en", help="Language code")
    args = parser.parse_args()
    
    generate_short(args.json, args.video, args.lang)
