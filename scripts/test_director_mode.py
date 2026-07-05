import os
import sys
import json
import argparse
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

def run_director_mode():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True, help='Path to lesson JSON file')
    parser.add_argument('--inspiration', type=str, required=True, help='Path to inspiration text file')
    parser.add_argument('--format', type=str, choices=['Short', 'Long'], required=True, help='Video format to generate')
    args = parser.parse_args()

    # Load JSON Data
    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found.")
        sys.exit(1)
    
    with open(args.input, "r", encoding="utf-8") as f:
        input_json_data = f.read()

    # Load Inspiration Data
    if not os.path.exists(args.inspiration):
        print(f"Error: {args.inspiration} not found.")
        sys.exit(1)
        
    with open(args.inspiration, "r", encoding="utf-8") as f:
        inspiration_data = f.read()

    # Define the System Prompt
    system_prompt = f"""
    You are the Creative Director and Lead Engineer for "Understanding AIML." 
    I am providing: 
    1. Technical Content: {input_json_data}
    2. YouTube Inspiration Strategy: {inspiration_data}
    3. Video Format: {args.format}

    REQUIREMENTS FOR ALL SCRIPTS:
    1. THE MISSING FACTORS (MUST INCLUDE):
       - Radical Transparency: If the technical content includes a coding task, intentionally script a "live bug" moment (e.g., an OOM error or dimension mismatch) and show the thought process to fix it. Do not just show the success.
       - Mental Model First: Start every complex topic with a vivid, non-technical analogy before diving into the architecture.
       - Active Challenge: If {args.format} is "Long", insert at least one "Pause & Solve" moment where you present a snippet and ask the viewer to identify the output or bug before you reveal it.

    2. FORMAT SPECIFIC LOGIC:
       - If {args.format} == "Short": 
         - Focus: High-velocity insight. 
         - Hook: Use the "Inspiration Data" to start with a controversial or surprising question.
         - Constraints: No intro, no fluff. 150 words max. End with a sharp, actionable "Pro Tip".
       - If {args.format} == "Long":
         - Focus: Deep-dive mastery.
         - Structure: Hook -> Mental Model Analogy -> Step-by-Step implementation (including the 'Radical Transparency' debugs) -> Active Challenge -> Recap.
         - Constraints: No slide limits. Allow the script to expand based on the complexity required to fully explain the mental model.

    3. OUTPUT FORMAT:
       - Script: Provide the output as a clean, segmented script structure labeled by [Visual] and [Audio] cues.
       - SEO & Metadata: At the end of the script, provide a YouTube optimized Title, Description, and Tags (for {args.format} format). 
       - Thumbnail: Provide a visual concept and the exact text that should go on the YouTube thumbnail to maximize CTR.
    """

    print("🎥 Calling Gemini Director Mode...")
    client = genai.Client()
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
        )
        
        output_file = "director_output.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"✅ Success! Script saved to {output_file}")
        
    except Exception as e:
        print(f"❌ Gemini generation failed: {e}")

if __name__ == "__main__":
    run_director_mode()
