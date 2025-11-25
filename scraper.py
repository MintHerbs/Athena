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

def get_video_stats_and_details(video_ids):
    """
    Fetches statistics (views) and details for a batch of video IDs.
    """
    VIDEOS_API_URL = "https://www.googleapis.com/youtube/v3/videos"
    
    # Join IDs with commas for batch request
    ids_string = ",".join(video_ids)
    
    params = {
        "key": API_KEY,
        "part": "snippet,statistics",
        "id": ids_string
    }
    
    try:
        r = requests.get(VIDEOS_API_URL, params=params).json()
        return r.get("items", [])
    except Exception as e:
        print(f"Error fetching video stats: {e}")
        return []

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
                clean_text = text.replace("\n", " ").replace("\r", "")
                comments.append(clean_text)
        return " | ".join(comments)
    except Exception:
        return ""

def run_scraper():
    """
    Main function to scrape data. 
    Returns a list of detailed dictionaries including channel info and stats.
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
        # 1. Get Channel Details & Uploads Playlist ID
        r = requests.get(CHANNELS_API_URL, params={
            "key": API_KEY, "part": "contentDetails,snippet", "id": channel_id
        }).json()
        
        if "items" not in r:
            continue
            
        uploads_id = r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        channel_name = r["items"][0]["snippet"]["title"]
        channel_url = f"https://www.youtube.com/channel/{channel_id}"

        print(f"Scraping channel: {channel_name}")

        # 2. Get Video IDs from Playlist
        playlist_params = {
            "key": API_KEY, "part": "snippet", "playlistId": uploads_id, "maxResults": 50
        }
        
        r = requests.get(PLAYLIST_API_URL, params=playlist_params).json()
        
        if "items" in r:
            # Extract video IDs to fetch stats in a batch (more efficient)
            video_ids = [item["snippet"]["resourceId"]["videoId"] for item in r["items"]]
            
            # 3. Fetch View Counts and Details
            video_details_list = get_video_stats_and_details(video_ids)
            
            for item in tqdm(video_details_list, desc=f"Processing {channel_name}"):
                vid_id = item["id"]
                title = item["snippet"]["title"]
                view_count = item["statistics"].get("viewCount", "0")
                
                # Fetch comments
                comments = get_comments(vid_id)
                
                if comments:
                    video_info = {
                        "video_id": vid_id,
                        "title": title,
                        "video_url": f"https://www.youtube.com/watch?v={vid_id}",
                        "channel_name": channel_name,
                        "channel_id": channel_id,
                        "channel_url": channel_url,
                        "views": view_count,
                        "comments": comments
                    }
                    all_video_data.append(video_info)
                
                time.sleep(0.1) 

    return all_video_data

if __name__ == "__main__":
    data = run_scraper()
    print(f"Scraped {len(data)} videos.")