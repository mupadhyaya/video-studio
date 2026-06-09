import os
import json
import datetime
from google import genai
from google.genai import types

def generate_lesson():
    print("Waking up Gemini Curriculum Director...")
    # The client automatically picks up the GEMINI_API_KEY from the environment
    client = genai.Client()
    
    start_date = datetime.date(2026, 6, 10)
    today = datetime.date.today()
    day_num = max(1, (today - start_date).days + 1)
    
    prompt = f"""
    You are the Lead Curriculum Director for an educational AI channel. Write Day {day_num} of our Retrieval-Augmented Generation (RAG) series.
    The output MUST be valid JSON matching this schema exactly. Do not wrap in markdown blocks.
    
    Requirements for a 2-minute video lecture:
    - Create exactly 4 slides in the storyboard array.
    - Each slide must have 3 to 5 detailed bullet points.
    - The narration for each slide should be in-depth and conversational, sounding like a real expert teaching a live class.
    - The total combined narration text across all slides must be around 300 words (which takes exactly 2 minutes to speak).

    {{
      "video_id": "rag_lesson_{day_num:03d}",
      "meta_title": "RAG Lesson {day_num}",
      "storyboard": [
        {{
          "slide_index": 1,
          "title": "[Engaging Slide Header]",
          "bullets": [
            "[Detailed Bullet 1]",
            "[Detailed Bullet 2]",
            "[Detailed Bullet 3]"
          ],
          "narration_text": "[Comprehensive, engaging conversational explanation for this slide]"
        }}
      ] # Note: Ensure you generate 4 objects in this array!
    }}
    """
    
    response = client.models.generate_content(
        model='gemini-2.0-flash',
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
