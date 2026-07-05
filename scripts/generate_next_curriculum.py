#!/usr/bin/env python3
import os
import json
import re
from dotenv import load_dotenv
load_dotenv()
from google import genai

def read_all_curriculums():
    covered_topics = []
    with open("curriculum.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            if line.endswith(".txt"):
                try:
                    with open(line, "r") as sub_f:
                        covered_topics.extend([sub_line.strip() for sub_line in sub_f if sub_line.strip()])
                except Exception:
                    pass
            else:
                covered_topics.append(line)
    return covered_topics

def generate_next_curriculum():
    print("Waking up Gemini Dean of AI...")
    client = genai.Client()
    
    covered_topics = read_all_curriculums()
    
    prompt = f"""
    You are the Dean of AI for an advanced educational YouTube channel.
    Your job is to design the next 15-day curriculum module for our learning series.
    
    Here is the exact list of ALL topics we have already covered in the past:
    {json.dumps(covered_topics, indent=2)}
    
    Based on what has already been covered, identify the next logical advanced topic in Artificial Intelligence, Machine Learning, or Agentic Systems.
    Generate exactly 15 highly technical, practical lessons for this new module.
    
    OUTPUT FORMAT:
    Output NOTHING but the 15 lesson topics, one per line. Do not number them. Do not include markdown formatting or introduction text.
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
    )
    
    new_topics = [t.strip() for t in response.text.strip().split('\n') if t.strip()]
    if not new_topics:
        raise ValueError("Gemini returned an empty curriculum.")
        
    # Generate a new filename
    import time
    timestamp = int(time.time())
    new_filename = f"auto_generated_curriculum_{timestamp}.txt"
    
    # Save the new curriculum
    with open(new_filename, "w", encoding="utf-8") as f:
        for topic in new_topics:
            # Strip numbering if the model accidentally included it
            clean_topic = re.sub(r'^\d+[\.\)]\s*', '', topic)
            f.write(f"{clean_topic}\n")
            
    print(f"✅ Generated new curriculum: {new_filename} with {len(new_topics)} topics.")
    
    # Append to curriculum.txt
    with open("curriculum.txt", "a", encoding="utf-8") as f:
        f.write(f"\n{new_filename}\n")
        
    print(f"✅ Appended {new_filename} to curriculum.txt")
    return new_filename

if __name__ == "__main__":
    generate_next_curriculum()
