#!/usr/bin/env python3
import os
import json
import asyncio
import argparse
import shutil
from core.image_engine import render_slide
from core.audio_engine import generate_speech
from core.compiler import compile_video


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
            img_path = os.path.join(images_dir, f"slide_{i}.png")

            # Extract language-specific fields, falling back to bare keys
            title = slide.get(f"title_{lang}", slide.get("title", f"Slide {i + 1}"))
            bullets = slide.get(f"bullets_{lang}", slide.get("content", []))

            print(f"  Rendering frame for slide {i + 1}: '{title}'...")
            render_slide(title, bullets, img_path)

        # --- Step 2: Synthesize narrations ---
        print(f"\nStep 2: Synthesizing [{lang.upper()}] narrations with edge-tts...")
        audio_tasks = []
        for i, slide in enumerate(lesson_data):
            narration = slide.get(f"narration_{lang}", slide.get("narration", ""))
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
            shutil.rmtree(temp_dir)


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
    args = parser.parse_args()

    # --- Validate input ---
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        return

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            lesson_data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse input JSON. Details: {e}")
        return

    if not isinstance(lesson_data, list):
        print("Error: Input JSON must be a list of slide objects.")
        return

    # --- Sequential dual-language build ---
    async def dual_build():
        en_path = f"{args.video_id}_en.mp4"
        hi_path = f"{args.video_id}_hi.mp4"

        await build_video_for_language(lesson_data, "en", args.theme, en_path)
        await build_video_for_language(lesson_data, "hi", args.theme, hi_path)

        print(f"\n{'='*60}")
        print("  All builds complete!")
        print(f"  English : {en_path}")
        print(f"  Hindi   : {hi_path}")
        print(f"{'='*60}")

        # --- Automatic YouTube Upload ---
        if "YOUTUBE_OAUTH_TOKEN" in os.environ:
            print("\n  [YOUTUBE] Valid OAuth token found in environment. Initiating upload...")
            from core.youtube_uploader import upload_video
            
            # Extract main title from the first slide
            base_title_en = lesson_data[0].get("title_en", "Daily Tech Update")
            base_title_hi = lesson_data[0].get("title_hi", "डेली टेक अपडेट")
            
            try:
                upload_video(en_path, {"meta_title": f"[EN] {base_title_en}"})
                upload_video(hi_path, {"meta_title": f"[HI] {base_title_hi}"})
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
