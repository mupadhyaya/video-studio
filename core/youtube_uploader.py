import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

def upload_video(video_path, metadata):
    token_str = os.environ.get("YOUTUBE_OAUTH_TOKEN")
    if not token_str:
        print("⚠️ YOUTUBE_OAUTH_TOKEN not found. Skipping upload. Video generated locally!")
        return

    print("Authenticating with YouTube API...")
    creds_info = json.loads(token_str)
    credentials = Credentials.from_authorized_user_info(creds_info)
    
    youtube = build("youtube", "v3", credentials=credentials)
    
    body = {
        "snippet": {
            "title": metadata.get("title", metadata.get("meta_title", "New AIML Lesson")),
            "description": metadata.get("description", "Daily automated tech curriculum update."),
            "tags": metadata.get("tags", ["AIML", "RAG", "Engineering", "Tutorial"]),
            "categoryId": "27" # Education Category
        },
        "status": {
            "privacyStatus": "private" # Uploads as a draft for your review
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    
    print(f"Uploading {video_path} to YouTube as a private draft...")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    video_id = response['id']
    print(f"✅ Success! Video deployed to channel. Video ID: {video_id}")
    
    # --- Upload Custom Thumbnail ---
    thumbnail_path = metadata.get("thumbnail_path")
    if thumbnail_path and os.path.exists(thumbnail_path):
        print(f"Uploading custom thumbnail from {thumbnail_path}...")
        thumb_media = MediaFileUpload(thumbnail_path, mimetype="image/png")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=thumb_media
            ).execute()
            print("✅ Custom thumbnail attached successfully!")
        except Exception as e:
            print(f"⚠️ Failed to upload thumbnail: {e}")
