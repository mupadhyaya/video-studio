import os
import json
import datetime
from google import genai
from google.genai import types

def generate_lesson():
    print("Waking up Gemini 2.5 Pro Curriculum Director...")
    # The client automatically picks up the GEMINI_API_KEY from the environment
    client = genai.Client()
    
    start_date = datetime.date(2026, 6, 10)
    today = datetime.date.today()
    day_num = max(1, (today - start_date).days + 1)
    
    prompt = f"""
    You are the Lead Curriculum Director for an educational AI channel. Write Day {day_num} of our Retrieval-Augmented Generation (RAG) series.
    The output MUST be valid JSON matching this schema exactly. Do not wrap in markdown blocks.
    {{
      "video_id": "rag_lesson_{day_num:03d}",
      "meta_title": "RAG Lesson {day_num}",
      "storyboard": [
        {{
          "slide_index": 1,
          "title": "[Slide Header]",
          "bullets": ["[Point 1]", "[Point 2]"],
          "narration_text": "[Clear, conversational explanation]"
        }}
      ]
    }}
    Ensure the lesson is highly educational, under 150 words total narration, and focuses on one core technical concept.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    
    os.makedirs("scripts", exist_ok=True)
    filename = f"scripts/{day_num:03d}_lesson.json"
    
    with open(filename, "w") as f:
        f.write(response.text)
        
    print(f"✅ Successfully generated {filename}")

if __name__ == "__main__":
    generate_lesson()
