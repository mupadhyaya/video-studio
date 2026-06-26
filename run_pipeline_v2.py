#!/usr/bin/env python3
import os
import json
import asyncio
import argparse
import shutil
from PIL import Image
from core.image_engine import render_slide
from core.audio_engine import generate_speech
from core.compiler_v2 import compile_video


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
                
                # Composite the Base Slide (which has the Title text rendered on it)
                thumb_img = Image.open(img_base_path).convert("RGBA")
                
                # Paste the avatar on the right side
                avatar_path = "assets/masked_hindi_rest.png" if lang == "hi" else "assets/masked_avatar_0.png"
                if os.path.exists(avatar_path):
                    avatar_img = Image.open(avatar_path).convert("RGBA")
                    # Scale avatar slightly if needed, or just paste it aligned to bottom right
                    paste_x = thumb_img.width - avatar_img.width - 50
                    paste_y = thumb_img.height - avatar_img.height
                    thumb_img.paste(avatar_img, (paste_x, paste_y), avatar_img)
                
                thumb_img.save(thumb_path)
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
                "description": yt_meta_en.get("description", "Daily automated tech curriculum update."),
                "tags": yt_meta_en.get("tags", ["AIML", "Tutorial", "AI"]),
                "thumbnail_path": os.path.join(input_dir, "thumbnail_en.png")
            }
            
            hi_upload_data = {
                "title": yt_meta_hi.get("title", f"[HI] {meta_title}"),
                "description": yt_meta_hi.get("description", "डेली ऑटोमेटेड टेक अपडेट।"),
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
