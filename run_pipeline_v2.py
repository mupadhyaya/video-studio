#!/usr/bin/env python3
import os
import json
import asyncio
import argparse
import shutil
from PIL import Image
from core.image_engine import render_slide, generate_thumbnail
from core.audio_engine import generate_speech
from core.compiler_v2 import compile_video
import urllib.parse
import urllib.request
from moviepy import AudioFileClip


async def build_video_for_language(lesson_data, lang, theme, output_path):
    """
    Builds a complete video for a single language track.

    Extracts `title_{lang}`, `bullets_{lang}`, and `narration_{lang}` keys from
    each slide object in the storyboard array.

    Args:
        lesson_data: List of slide dicts from the JSON storyboard.
        lang: Language code string ("en" or "hi").
        theme: Reserved for future theme customisation (unused for now).
        output_path: Destination path for the compiled MP4.
    """
    print(f"\n{'='*60}")
    print(f"  Building [{lang.upper()}] video → {output_path}")
    print(f"{'='*60}")

    # Create per-language temp directories
    temp_dir = os.path.abspath(f"temp_build_{lang}")
    images_dir = os.path.join(temp_dir, "images")
    audio_dir = os.path.join(temp_dir, "audio")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)

    try:
        # --- Step 1: Render slide frames ---
        print(f"Step 1: Rendering [{lang.upper()}] slide images with Pillow...")
        for i, slide in enumerate(lesson_data):
            img_base_path = os.path.join(images_dir, f"slide_{i}_base.png")
            img_content_path = os.path.join(images_dir, f"slide_{i}_content.png")

            # Extract language-specific fields, falling back to bare keys
            title = slide.get(f"title_{lang}", slide.get("title", f"Slide {i + 1}"))
            content_text = slide.get(f"content_text_{lang}", slide.get("content_text", slide.get("content", "")))
            visual_type = slide.get("visual_type", "")
            visual_content = slide.get("visual_content", "")

            print(f"  Rendering frame for slide {i + 1}: '{title}'...")
            render_slide(title, content_text, visual_type, visual_content, img_base_path, img_content_path)
            
            # --- Thumbnail Extraction ---
            if visual_type == "title_slide":
                print(f"  [THUMBNAIL] Extracting Title Slide as Thumbnail...")
                thumb_path = os.path.join(os.path.dirname(os.path.abspath(output_path)), f"thumbnail_{lang}.png")
                avatar_path = "assets/masked_hindi_rest.png" if lang == "hi" else "assets/masked_avatar_0.png"
                generate_thumbnail(title, thumb_path, avatar_path)
                print(f"  [THUMBNAIL] Saved custom thumbnail to: {thumb_path}")
                print(f"  [THUMBNAIL] Saved custom thumbnail to: {thumb_path}")

        # --- Step 2: Synthesize narrations ---
        print(f"\nStep 2: Synthesizing [{lang.upper()}] narrations with edge-tts...")
        audio_tasks = []
        for i, slide in enumerate(lesson_data):
            narration = slide.get(f"narration_text_{lang}", slide.get(f"narration_{lang}", slide.get("narration_text", slide.get("narration", ""))))
            if not narration.strip():
                narration = "Slide detail."

            audio_path = os.path.join(audio_dir, f"audio_{i}.mp3")
            print(f"  Generating narration for slide {i + 1}...")
            audio_tasks.append(generate_speech(narration, audio_path, lang_code=lang))

        await asyncio.gather(*audio_tasks)

        # --- Step 2.5: Auto-Timestamps & Exports ---
        print(f"\nStep 2.5: Generating timestamps and exporting resources...")
        
        # Create an exports folder
        exports_dir = os.path.join(os.path.dirname(os.path.abspath(output_path)), "exports")
        os.makedirs(exports_dir, exist_ok=True)
        
        timestamps = ["\n📌 Timestamps:"]
        resources = ["\n📥 Downloadable Resources:"]
        
        current_time = 0.0
        for i, slide in enumerate(lesson_data):
            # Timestamps
            title = slide.get(f"title_{lang}", slide.get("title", f"Slide {i + 1}"))
            mins = int(current_time // 60)
            secs = int(current_time % 60)
            timestamps.append(f"{mins}:{secs:02d} - {title}")
            
            # Read audio duration
            audio_path = os.path.join(audio_dir, f"audio_{i}.mp3")
            with AudioFileClip(audio_path) as audio_clip:
                current_time += audio_clip.duration
                
            # Exports & TinyURL
            visual_type = slide.get("visual_type", "")
            visual_content = slide.get("visual_content", "")
            video_id = os.path.basename(output_path).replace(f"_{lang}.mp4", "")
            
            file_name = None
            file_path = None
            if visual_type == "code_snippet":
                file_name = f"{video_id}_slide_{i}.py"
                file_path = os.path.join(exports_dir, file_name)
                with open(file_path, "w") as f:
                    f.write(str(visual_content))
            elif visual_type in ["architecture_diagram", "sequence_diagram"]:
                # Save the Mermaid raw code to a .mmd file
                file_name = f"{video_id}_slide_{i}.mmd"
                file_path = os.path.join(exports_dir, file_name)
                with open(file_path, "w") as f:
                    f.write(str(visual_content))
            
            if file_name:
                print(f"  Exported {file_name}")
                # The user wants this to be on the public rag-learning-series repo
                raw_github_url = f"https://raw.githubusercontent.com/mupadhyaya/rag-learning-series/main/assets/{file_name}"
                try:
                    tiny_url = urllib.request.urlopen("http://tinyurl.com/api-create.php?url=" + urllib.parse.quote(raw_github_url)).read().decode("utf-8")
                    resources.append(f"- {title} ({file_name}): {tiny_url}")
                except Exception as e:
                    print(f"  Failed to generate TinyURL: {e}")
                    resources.append(f"- {title}: {raw_github_url}")

        # Store these in lesson_data for the YouTube uploader to pick up
        if not isinstance(lesson_data, list) or len(lesson_data) == 0:
            pass
        else:
            lesson_data[0][f"generated_timestamps_{lang}"] = "\n".join(timestamps)
            lesson_data[0][f"generated_resources_{lang}"] = "\n".join(resources)

        # --- Step 3: Compile video ---
        print(f"\nStep 3: Compiling [{lang.upper()}] slide sequence into video...")
        compile_video(lesson_data, images_dir, audio_dir, output_path)
        print(f"[{lang.upper()}] Video saved to: {output_path}")

    finally:
        if os.path.exists(temp_dir):
            print(f"Cleaning up [{lang.upper()}] intermediate build assets...")
            # shutil.rmtree(temp_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Video Studio — Dual-Language Presentation Pipeline"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to structured JSON storyboard file.",
    )
    parser.add_argument(
        "--video-id",
        default="presentation",
        help="Base name for output files (produces {video_id}_en.mp4, {video_id}_hi.mp4).",
    )
    parser.add_argument(
        "--theme",
        default="dark",
        help="Visual theme preset (reserved for future use).",
    )
    parser.add_argument(
        "--lang",
        default="all",
        choices=["en", "hi", "all"],
        help="Language to render (en, hi, or all).",
    )
    args = parser.parse_args()

    # --- Validate input ---
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        return

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse input JSON. Details: {e}")
        return

    meta_title = "Daily Tech Update"
    if isinstance(raw_data, dict):
        meta_title = raw_data.get("meta_title", meta_title)
        lesson_data = raw_data.get("storyboard", raw_data)
    else:
        lesson_data = raw_data

    if not isinstance(lesson_data, list):
        print("Error: Input JSON must be a list of slide objects.")
        return

    # --- Sequential dual-language build ---
    async def dual_build():
        input_dir = os.path.dirname(os.path.abspath(args.input))
        en_path = os.path.join(input_dir, f"{args.video_id}_en.mp4")
        hi_path = os.path.join(input_dir, f"{args.video_id}_hi.mp4")

        if args.lang in ["en", "all"]:
            await build_video_for_language(lesson_data, "en", args.theme, en_path)
            
        if args.lang in ["hi", "all"]:
            await build_video_for_language(lesson_data, "hi", args.theme, hi_path)

        print(f"\n{'='*60}")
        print("  All builds complete!")
        if args.lang in ["en", "all"]: print(f"  English : {en_path}")
        if args.lang in ["hi", "all"]: print(f"  Hindi   : {hi_path}")
        print(f"{'='*60}")

        # --- Automatic YouTube Upload ---
        if "YOUTUBE_OAUTH_TOKEN" in os.environ:
            print("\n  [YOUTUBE] Valid OAuth token found in environment. Initiating upload...")
            from core.youtube_uploader import upload_video
            
            yt_meta_en = raw_data.get("youtube_metadata_en", {})
            yt_meta_hi = raw_data.get("youtube_metadata_hi", {})
            
            en_upload_data = {
                "title": yt_meta_en.get("title", f"[EN] {meta_title}"),
                "description": yt_meta_en.get("description", "Daily automated tech curriculum update.") + "\n" + lesson_data[0].get("generated_timestamps_en", "") + "\n" + lesson_data[0].get("generated_resources_en", ""),
                "tags": yt_meta_en.get("tags", ["AIML", "Tutorial", "AI"]),
                "thumbnail_path": os.path.join(input_dir, "thumbnail_en.png")
            }
            
            hi_upload_data = {
                "title": yt_meta_hi.get("title", f"[HI] {meta_title}"),
                "description": yt_meta_hi.get("description", "डेली ऑटोमेटेड टेक अपडेट।") + "\n" + lesson_data[0].get("generated_timestamps_hi", "") + "\n" + lesson_data[0].get("generated_resources_hi", ""),
                "tags": yt_meta_hi.get("tags", ["AIML", "Tutorial", "AI in Hindi"]),
                "thumbnail_path": os.path.join(input_dir, "thumbnail_hi.png")
            }
            
            try:
                upload_video(en_path, en_upload_data)
                upload_video(hi_path, hi_upload_data)
            except Exception as e:
                print(f"  [ERROR] YouTube upload failed: {e}")
        else:
            print("\n  [YOUTUBE] Skipping upload (YOUTUBE_OAUTH_TOKEN not set).")

    try:
        asyncio.run(dual_build())
    except Exception as e:
        print(f"\nError: Pipeline execution failed. Details: {e}")


if __name__ == "__main__":
    main()
