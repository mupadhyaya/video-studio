#!/usr/bin/env python3
"""
generate_daily_script.py

Uses the Gemini 1.5 Pro model to generate a dual-language (English + Hindi)
curriculum lesson script and saves it as a dated JSON file in scripts/.
"""

import os
import json
import datetime
from google import genai
from google.genai import types

# ── Configuration ────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-1.5-flash"
OUTPUT_DIR = "scripts"
CURRICULUM_FILE = "curriculum.txt"

SYSTEM_PROMPT_TEMPLATE = """\
You are a Curriculum Director specialising in AI & Machine Learning education.
Your task is to write a concise, 2-minute introductory lesson suitable for a
narrated slide-deck video.

Today's topic: **{topic}**

Requirements:
- Produce exactly 3 slides.
- Each slide must contain a title, 2-4 bullet points, and a narration paragraph.
- Provide ALL content in BOTH English and Hindi.
- The narration for each slide should be roughly 20-30 seconds when spoken aloud.
- Keep bullet text short (≤15 words per bullet).

You MUST respond with ONLY valid JSON — no markdown fences, no commentary.
The JSON must be an array of objects with exactly these keys per object:
  "title_en", "title_hi",
  "bullets_en" (array of strings), "bullets_hi" (array of strings),
  "narration_en" (string), "narration_hi" (string)
"""

def get_next_topic():
    if not os.path.exists(CURRICULUM_FILE):
        return None
    
    with open(CURRICULUM_FILE, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        
    if not lines:
        return None
        
    topic = lines.pop(0)
    
    with open(CURRICULUM_FILE, "w") as f:
        for line in lines:
            f.write(f"{line}\n")
            
    return topic


def main():
    # ── Get Topic ────────────────────────────────────────────────────────────
    topic = get_next_topic()
    if not topic:
        print("Error: No more topics found in curriculum.txt!")
        return

    print(f"Today's topic is: {topic}")
    prompt = SYSTEM_PROMPT_TEMPLATE.format(topic=topic)

    # ── Authenticate ─────────────────────────────────────────────────────────
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set. "
            "Export it or pass it via GitHub Actions secrets."
        )
    client = genai.Client(api_key=api_key)

    # ── Call Gemini ──────────────────────────────────────────────────────────
    print(f"Calling {GEMINI_MODEL} for today's lesson script...")

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            response_mime_type="application/json",
        ),
    )

    raw_text = response.text.strip()

    # ── Parse & validate ─────────────────────────────────────────────────────
    try:
        lesson_data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"Error: Gemini returned invalid JSON.\n{raw_text[:500]}")
        raise e

    if not isinstance(lesson_data, list):
        raise ValueError("Expected a JSON array of slide objects.")

    required_keys = {
        "title_en", "title_hi",
        "bullets_en", "bullets_hi",
        "narration_en", "narration_hi",
    }
    for i, slide in enumerate(lesson_data):
        missing = required_keys - set(slide.keys())
        if missing:
            raise ValueError(
                f"Slide {i} is missing required keys: {missing}"
            )

    # ── Save to scripts/ ─────────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = datetime.date.today().isoformat()  # YYYY-MM-DD
    output_path = os.path.join(OUTPUT_DIR, f"{today}_lesson.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(lesson_data, f, ensure_ascii=False, indent=2)

    print(f"Lesson script saved to: {output_path}")
    print(f"Slides generated: {len(lesson_data)}")


if __name__ == "__main__":
    main()
