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
            "tags": metadata.get("tags", ["AIML", "RAG", "Engineering", "Tutorial", "Python"]),
            "categoryId": "28" # Science & Technology Category
        },
        "status": {
            "privacyStatus": "private", # Uploads as a draft for your review
            "selfDeclaredMadeForKids": False
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
            
    # --- Upload Subtitles (SRT) ---
    srt_path = metadata.get("srt_path")
    if srt_path and os.path.exists(srt_path):
        print(f"Uploading subtitles from {srt_path}...")
        try:
            caption_insert_request = youtube.captions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "language": metadata.get("lang", "en"),
                        "name": metadata.get("lang_name", "English"),
                        "isDraft": False
                    }
                },
                media_body=MediaFileUpload(srt_path, mimetype="text/srt")
            )
            caption_insert_request.execute()
            print("✅ Subtitles attached successfully!")
        except Exception as e:
            print(f"⚠️ Failed to upload subtitles: {e}")
