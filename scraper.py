import os
import requests
import yaml
import time
from tqdm import tqdm
from dotenv import load_dotenv

# Load config and env vars immediately
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_config():
    with open("config.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def process_video_details(video_snippet):
    """Extracts ID and Title"""
    return {
        "video_id": video_snippet["resourceId"]["videoId"],
        "title": video_snippet["title"]
    }

def get_comments(video_id):
    """Fetches top 100 comments for a specific video ID"""
    COMMENTS_API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "key": API_KEY,
        "part": "snippet",
        "videoId": video_id,
        "maxResults": 100,
        "textFormat": "plainText",
        "order": "relevance"
    }
    
    try:
        r = requests.get(COMMENTS_API_URL, params=params).json()
        comments = []
        if "items" in r:
            for item in r["items"]:
                text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                # Clean text to remove newlines for cleaner processing later
                clean_text = text.replace("\n", " ").replace("\r", "")
                comments.append(clean_text)
        return " | ".join(comments)
    except Exception:
        return ""

def run_scraper():
    """
    Main function to scrape data. 
    Returns a list of dictionaries.
    """
    if not API_KEY:
        raise ValueError("Missing YOUTUBE_API_KEY in environment.")

    config = get_config()
    channel_ids = config["channel_ids"]
    
    all_video_data = []

    CHANNELS_API_URL = "https://www.googleapis.com/youtube/v3/channels"
    PLAYLIST_API_URL = "https://www.googleapis.com/youtube/v3/playlistItems"

    print("--- Starting YouTube Scraper ---")

    for channel_id in channel_ids:
        # 1. Get Uploads Playlist ID
        r = requests.get(CHANNELS_API_URL, params={
            "key": API_KEY, "part": "contentDetails,snippet", "id": channel_id
        }).json()
        
        if "items" not in r:
            continue
            
        uploads_id = r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        channel_name = r["items"][0].get("snippet", {}).get("title", "Unknown Channel")

        print(f"Scraping channel: {channel_name}")

        # 2. Get Videos from Playlist
        playlist_params = {
            "key": API_KEY, "part": "snippet", "playlistId": uploads_id, "maxResults": 50
        }
        
        r = requests.get(PLAYLIST_API_URL, params=playlist_params).json()
        
        if "items" in r:
            # We use tqdm here to show progress for this specific channel
            for item in tqdm(r["items"], desc=f"Processing {channel_name}"):
                video_info = process_video_details(item["snippet"])
                
                # Fetch comments for this video
                video_comments = get_comments(video_info["video_id"])
                
                if video_comments:
                    video_info["comments"] = video_comments
                    all_video_data.append(video_info)
                
                time.sleep(0.1) # Respect API limits

    return all_video_data

# ==========================================
# IMPORTANT: This protects the code from running on import
# ==========================================
if __name__ == "__main__":
    # This block only runs if you type "py scraper.py" in the terminal
    # It DOES NOT run if you type "py app.py"
    data = run_scraper()
    print(f"Scraped {len(data)} videos.")