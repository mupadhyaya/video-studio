#!/usr/bin/env python3
import os
import json
import asyncio
import argparse
import shutil
from core.image_engine import render_slide
from core.audio_engine import generate_speech
from core.compiler import compile_video

async def process_slide_audio(slide, index, audio_dir):
    """
    Asynchronously generates TTS audio file for a slide.
    """
    audio_path = os.path.join(audio_dir, f"audio_{index}.mp3")
    narration = slide.get("narration", "")
    if not narration.strip():
        # Fallback if narration is empty to prevent edge-tts from failing
        narration = "Slide detail."
    
    print(f"Generating narration for slide {index + 1}...")
    await generate_speech(narration, audio_path)

async def run_async_pipeline(slides_data, images_dir, audio_dir, output_path):
    # 1. Render slide canvas frames
    print("Step 1: Rendering slide images with Pillow...")
    for i, slide in enumerate(slides_data):
        img_path = os.path.join(images_dir, f"slide_{i}.png")
        title = slide.get("title", f"Slide {i + 1}")
        content = slide.get("content", [])
        print(f"Rendering frame for slide {i + 1}: '{title}'...")
        render_slide(title, content, img_path)

    # 2. Render speech voiceover files asynchronously
    print("\nStep 2: Synthesizing slide narrations with edge-tts...")
    tasks = []
    for i, slide in enumerate(slides_data):
        tasks.append(process_slide_audio(slide, i, audio_dir))
    
    await asyncio.gather(*tasks)

    # 3. Stitch and compile video
    print("\nStep 3: Compiling slide sequence into final video output...")
    compile_video(slides_data, images_dir, audio_dir, output_path)

def main():
    parser = argparse.ArgumentParser(description="Video Studio Presentation Generation Orchestrator")
    parser.add_argument(
        "--input", 
        required=True, 
        help="Path to structured JSON configuration file containing slide content and narration."
    )
    parser.add_argument(
        "--output", 
        default="output.mp4", 
        help="Output path for the compiled MP4 presentation file."
    )
    args = parser.parse_args()

    # Verify input exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        return

    # Load slides configuration
    try:
        with open(args.input, "r") as f:
            slides_data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse input JSON file. Details: {e}")
        return

    if not isinstance(slides_data, list):
        print("Error: Input JSON must be a list of slide objects.")
        return

    # Create temporary directories for intermediate rendering assets
    temp_dir = os.path.abspath("temp_build")
    images_dir = os.path.join(temp_dir, "images")
    audio_dir = os.path.join(temp_dir, "audio")
    
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)

    try:
        # Run orchestrator tasks
        asyncio.run(run_async_pipeline(slides_data, images_dir, audio_dir, args.output))
        print(f"\nPipeline compilation completed successfully! Video saved to: {args.output}")
    except Exception as e:
        print(f"\nError: Pipeline execution failed. Details: {e}")
    finally:
        # Cleanup temporary files
        if os.path.exists(temp_dir):
            print("Cleaning up intermediate build assets...")
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
