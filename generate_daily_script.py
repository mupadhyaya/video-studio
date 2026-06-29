import os
from dotenv import load_dotenv
load_dotenv()
import json
import datetime
from google import genai
from google.genai import types

import argparse

def generate_lesson():
    parser = argparse.ArgumentParser()
    parser.add_argument('--day', type=int, help='Specific day number to generate (1-indexed)')
    args = parser.parse_args()

    print("Waking up Gemini Curriculum Director...")
    # The client automatically picks up the GEMINI_API_KEY from the environment
    client = genai.Client()
    
    if args.day:
        day_num = args.day
    else:
        # We use June 25, 2026 as the launch date for the series
        start_date = datetime.date(2026, 6, 25)
        today = datetime.date.today()
        day_num = max(1, (today - start_date).days + 1)
    
    topics = []
    with open("curriculum.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            if line.endswith(".txt"):
                try:
                    with open(line, "r") as sub_f:
                        topics.extend([{"topic": sub_line.strip(), "source": line} for sub_line in sub_f if sub_line.strip()])
                except Exception:
                    pass
            else:
                topics.append({"topic": line, "source": "rag_curriculum.txt"})
    
    # Wrap around if day_num exceeds available topics
    topic_index = (day_num - 1) % len(topics)
    current_topic_info = topics[topic_index]
    current_topic = current_topic_info["topic"]
    current_source = current_topic_info["source"]
    next_topic = topics[(topic_index + 1) % len(topics)]["topic"]
    
    prompt = f"""
    You are the Lead Curriculum Director for an educational AI channel. 
    Write a comprehensive, multi-slide lesson for our series. 
    The topic for today is: "{current_topic}"
    The next upcoming lecture will be: "{next_topic}"
    
    The output MUST be valid JSON matching this schema exactly.
    
    Requirements for the video lecture:
    - Create as many slides as needed to comprehensively cover the topic with high-quality, Senior Principal Engineer-level depth. Do not rush the content!
    - Each slide must have a single `content_text` block instead of bullet points. This should be a highly engaging paragraph (2-3 sentences) emphasizing real-world case studies, actionable insights, and data-driven examples.
    - The narration for each slide should be in-depth, conversational, and impactful, avoiding fluff. Hook the viewer immediately!
    - IMPORTANT: During the narration of the final slide, you MUST explicitly mention and tease the next upcoming lecture topic: "{next_topic}".
    - The video should be a deep-dive. Generate enough slides and narration so the total script is approximately 1000-1500 words (about 8-10 minutes of speaking time).
    - You must analyze the topic and decide the best visual aid. You MUST heavily prioritize generating a 'code_snippet', 'architecture_diagram', or 'sequence_diagram' to make the content highly valuable for professionals.
    - If you choose 'code_snippet', the code MUST be production-grade, highly accurate, and syntactically correct Python code. Never hallucinate fake libraries or methods. Focus on best practices!
    - If you generate a 'code_snippet' or diagram, you MUST instruct the viewer in the narration to "check the link in the description to download the architecture diagram and script".
    - IMPORTANT: Every time you generate a 'code_snippet', you MUST immediately follow it with a new slide whose `visual_type` is 'terminal_output'. The `visual_content` for this slide must be the expected realistic terminal output (e.g., standard output, logs) when running the preceding Python script.
    - If you choose 'architecture_diagram' or 'sequence_diagram', the `visual_content` MUST be valid, raw Mermaid.js code. IMPORTANT: Always use double quotes for node labels in Mermaid (e.g., `A["Text with [brackets] or special chars"]`) to avoid syntax errors!
    - The Hindi narration should be spoken by a female presenter. You MUST use feminine conjugations and pronouns (e.g., use 'मिलूंगी' instead of 'मिलूंगा', 'करूंगी' instead of 'करूंगा').

    {{
      "video_id": "lesson_{day_num:03d}",
      "meta_title": "{current_topic}",
      "youtube_metadata_en": {{
        "title": "[An engaging, search-optimized English YouTube title for this topic]",
        "description": "[A detailed YouTube description including a summary and what they will learn. (We will automatically append the code download links later)]",
        "tags": ["AI", "Tutorial", "list of 5 to 10 relevant tags"]
      }},
      "youtube_metadata_hi": {{
        "title": "[An engaging, search-optimized Hindi YouTube title for this topic]",
        "description": "[The exact same detailed YouTube description translated beautifully to Hindi. Also translate the github link sentence.]",
        "tags": ["AI in Hindi", "Hindi Tutorial", "list of 5 to 10 relevant tags"]
      }},
      "storyboard": [
        {{
          "slide_index": 1,
          "title_en": "[Engaging Slide Header in English]",
          "title_hi": "[Engaging Slide Header translated to Hindi]",
          "content_text_en": "[A single paragraph explaining the core concept in English.]",
          "content_text_hi": "[The exact same paragraph translated perfectly to conversational Hindi.]",
          "narration_text_en": "[Conversational explanation for this slide in English]",
          "narration_text_hi": "[The exact same conversational explanation translated to Hindi]",
          "visual_type": "[Must be exactly 'code_snippet', 'architecture_diagram', 'sequence_diagram', 'concept_box', or 'terminal_output']",
          "visual_content": "[If 'code_snippet', provide working Python code. If 'terminal_output', provide simulated terminal output. If 'architecture_diagram', raw Mermaid.js code. If 'concept_box', provide a short analogy. (Leave code/Mermaid/analogy/output in English)]"
        }}
      ]
    }}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    
    base_name = current_source.replace("_curriculum.txt", "").replace(".txt", "")
    series_dir = f"{base_name}_learning_series"
    out_dir = f"{series_dir}/lesson_{day_num:03d}"
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{out_dir}/lesson_{day_num:03d}.json"
    
    import json
    import re
    try:
        clean_text = re.sub(r'^```json\s*', '', response.text.strip())
        clean_text = re.sub(r'\s*```$', '', clean_text)
        data = json.loads(clean_text)
        storyboard = data.get("storyboard", [])
        
        yt_meta_hi = data.get("youtube_metadata_hi", {})
        
        title_slide = {
            "title_en": current_topic,
            "title_hi": yt_meta_hi.get("title", current_topic),
            "content_text_en": f"Welcome to the {base_name.replace('_', ' ').title()} Series",
            "content_text_hi": f"{base_name.replace('_', ' ').title()} सीरीज में आपका स्वागत है",
            "visual_type": "title_slide",
            "visual_content": current_topic,
            "narration_text_en": f"Welcome! Today we are discussing {current_topic}.",
            "narration_text_hi": f"आपका स्वागत है! आज हम {current_topic} पर चर्चा कर रहे हैं।"
        }
        
        agenda_slide = {
            "title_en": "Series Curriculum Map",
            "title_hi": "सीरीज पाठ्यक्रम मानचित्र",
            "content_text_en": "Tracking our progress through the Learning Series.",
            "content_text_hi": "लर्निंग सीरीज के माध्यम से हमारी प्रगति को ट्रैक करना।",
            "visual_type": "curriculum_map",
            "visual_content": json.dumps({
                "past": [t["topic"] for t in topics[:topic_index]],
                "present": current_topic,
                "future": [t["topic"] for t in topics[topic_index+1:]]
            }),
            "narration_text_en": "Here is a quick look at where we are in our curriculum.",
            "narration_text_hi": "यहां हमारे पाठ्यक्रम की एक झलक है।"
        }
        
        storyboard.insert(0, agenda_slide)
        storyboard.insert(0, title_slide)
        data["storyboard"] = storyboard
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        for slide in storyboard:
            if slide.get("visual_type") == "code_snippet":
                snippet_code = slide.get("visual_content", "").strip()
                if snippet_code:
                    # Strip python markdown if model accidentally included it
                    snippet_code = re.sub(r'^```python\s*', '', snippet_code)
                    snippet_code = re.sub(r'\s*```$', '', snippet_code)
                    snippet_file = f"{out_dir}/snippet_{slide.get('slide_index')}.py"
                    with open(snippet_file, "w", encoding="utf-8") as sf:
                        sf.write(snippet_code)
                    print(f"Extracted python snippet to {snippet_file}")
                    
    except Exception as e:
        print(f"Failed to parse or inject agenda slide: {e}")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.text)
        
    print(f"✅ Successfully generated {filename}")

    github_env = os.environ.get('GITHUB_ENV')
    if github_env:
        with open(github_env, 'a') as env_file:
            env_file.write(f"LESSON_DIR={out_dir}\n")
            env_file.write(f"VIDEO_ID=lesson_{day_num:03d}\n")
            env_file.write(f"SERIES_DIR={series_dir}\n")

if __name__ == "__main__":
    generate_lesson()
