import os
import json
import argparse
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google import genai

def fetch_inspiration(topic):
    print(f"🔍 Researching YouTube for topic: {topic}")
    api_key = os.environ.get("YOUTUBE_API_KEY")
    token_str = os.environ.get("YOUTUBE_OAUTH_TOKEN")
    
    if not api_key and not token_str:
        print("⚠️ Neither YOUTUBE_API_KEY nor YOUTUBE_OAUTH_TOKEN found. Skipping automated YouTube research.")
        # Write a generic fallback inspiration to unblock the pipeline
        fallback = f"Focus on delivering a high-quality, dense tutorial about {topic}. Use standard technical hooks."
        with open("inspiration.txt", "w", encoding="utf-8") as f:
            f.write(fallback)
        return
        
    try:
        if api_key:
            print("🔑 Using YOUTUBE_API_KEY for authentication.")
            youtube = build("youtube", "v3", developerKey=api_key)
        else:
            print("🔑 Using YOUTUBE_OAUTH_TOKEN for authentication.")
            creds_info = json.loads(token_str)
            credentials = Credentials.from_authorized_user_info(creds_info)
            youtube = build("youtube", "v3", credentials=credentials)
        
        # Search for top videos
        request = youtube.search().list(
            q=topic,
            part="snippet",
            type="video",
            order="viewCount",
            maxResults=5
        )
        response = request.execute()
        
        raw_data = "Here are the top performing YouTube videos on this topic:\n\n"
        for i, item in enumerate(response.get("items", [])):
            snippet = item["snippet"]
            raw_data += f"{i+1}. Title: {snippet['title']}\n"
            raw_data += f"   Channel: {snippet['channelTitle']}\n"
            raw_data += f"   Description: {snippet['description']}\n\n"
            
        print("🧠 Analyzing results with Gemini...")
        client = genai.Client()
        
        system_prompt = f"""
        You are a Master YouTube Strategist. I am providing you with the titles and descriptions of the top 5 most viewed videos for the topic: "{topic}".
        
        Analyze this raw data to figure out what hooks, angles, and keywords are currently working best.
        Then, generate a concise, highly actionable "YouTube Inspiration Strategy" that I can use to script my own video on this topic.
        
        Your output should include:
        1. The best hook angle to use (e.g., negative framing, tutorial, secret reveal).
        2. Keywords we must include.
        3. A visual concept for the thumbnail that stands out against these competitors.
        
        RAW YOUTUBE DATA:
        {raw_data}
        """
        
        ai_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
        )
        
        with open("inspiration.txt", "w", encoding="utf-8") as f:
            f.write(ai_response.text)
            
        print("✅ Successfully generated inspiration.txt based on real-time YouTube data!")
        
    except Exception as e:
        print(f"❌ Failed to fetch inspiration: {e}")
        with open("inspiration.txt", "w", encoding="utf-8") as f:
            f.write(f"Focus on delivering a high-quality, dense tutorial about {topic}. Use standard technical hooks.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True, help="Topic to research on YouTube")
    args = parser.parse_args()
    fetch_inspiration(args.topic)
