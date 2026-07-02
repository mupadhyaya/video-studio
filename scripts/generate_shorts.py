import os
import sys
import json
import argparse
from moviepy.editor import VideoFileClip, TextClip, ColorClip, CompositeVideoClip

def generate_short(json_path, video_path, lang="en"):
    print(f"🎬 Generating YouTube Short for {video_path}...")
    
    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        
    lesson_data = raw_data.get("storyboard", raw_data)
    
    # 1. Calculate timestamps for all slides to find the "best" hook slide
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(json_path)), f"temp_build_{lang}")
    if not os.path.exists(audio_dir):
        print(f"Warning: audio dir {audio_dir} not found. Cannot calculate timestamps.")
        return
        
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    
    current_time = 0.0
    best_slide_idx = -1
    best_slide_score = -1
    best_start = 0.0
    best_end = 0.0
    
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
            highlight = main_video.subclip(best_start, best_end)
            
            # Letterbox the 16:9 video inside a 9:16 vertical canvas (1080x1920)
            resized_highlight = highlight.resize(width=1080)
            
            # Background
            bg = ColorClip(size=(1080, 1920), color=(15, 15, 20), duration=highlight.duration)
            
            # Header
            header_text = TextClip("Understanding AIML", fontsize=80, color='white', font='Arial-Bold')
            header = header_text.set_position(('center', 200)).set_duration(highlight.duration)
            
            # Subheader
            slide_title = lesson_data[best_slide_idx].get(f"title_{lang}", lesson_data[best_slide_idx].get("title", ""))
            subheader_text = TextClip(slide_title, fontsize=50, color='#00FFCC', font='Arial')
            subheader = subheader_text.set_position(('center', 300)).set_duration(highlight.duration)
            
            # Footer CTA
            cta_text = TextClip("👇 Full Tutorial Link in Description 👇", fontsize=55, color='yellow', font='Arial-Bold')
            cta = cta_text.set_position(('center', 1600)).set_duration(highlight.duration)
            
            # Position video in exact center
            video_y_pos = (1920 - resized_highlight.h) / 2
            positioned_video = resized_highlight.set_position(('center', video_y_pos))
            
            final = CompositeVideoClip([bg, positioned_video, header, subheader, cta])
            
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
