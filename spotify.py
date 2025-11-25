import os
import requests
import json
import base64
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
OUTPUT_FILE = "spotify_analysis_results.json"

if not CLIENT_ID or not CLIENT_SECRET:
    # Set a flag to disable Spotify analysis if credentials are missing
    print("WARNING: Spotify credentials not found in .env. Skipping Spotify analysis.")
    SPOTIFY_ENABLED = False
else:
    SPOTIFY_ENABLED = True

# --- Spotify API Functions ---

def get_spotify_token():
    """Retrieves an access token from the Spotify API."""
    if not SPOTIFY_ENABLED:
        return None
        
    auth_url = "https://accounts.spotify.com/api/token"
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    try:
        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status() # Raise exception for bad status codes
        json_data = response.json()
        return json_data.get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting Spotify token: {e}")
        return None

def search_spotify(token, song_title, channel_name):
    """
    Searches Spotify for a track by combining the video title and channel name.
    """
    if not token:
        return None
        
    base_url = "https://api.spotify.com/v1/search"
    
    # Clean the title (e.g., removing text in parentheses)
    clean_title = song_title.split("(")[0].strip()
    
    # Combine title and channel name into a search query string (e.g., "title artist")
    # This greatly improves accuracy over just the title.
    search_query = f"track:{clean_title} artist:{channel_name}" # <-- USING CHANNEL NAME
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "q": search_query,
        "type": "track",
        "limit": 1 # Only interested in the best match
    }
    
    try:
        response = requests.get(base_url, headers=headers, params=params).json()
        
        tracks = response.get("tracks", {}).get("items")
        if tracks:
            track = tracks[0]
            artist_name = track["artists"][0]["name"] if track["artists"] else "Unknown Artist"
            
            return {
                "spotify_id": track["id"],
                "name": track["name"],
                "artist": artist_name,
                "popularity": track["popularity"],
                "link": track["external_urls"]["spotify"]
            }
        else:
            return None
    except Exception as e:
        print(f"Error searching Spotify for '{search_query}': {e}")
        return None

def run_spotify_analysis(video_data_list):
    """
    Main function called by app.py.
    Takes a list of video dicts, finds them on Spotify, and saves results.
    """
    if not SPOTIFY_ENABLED:
        print("Spotify analysis skipped due to missing credentials.")
        return []

    print("\n--- Starting Spotify Analysis ---")
    token = get_spotify_token()
    if not token:
        print("Failed to get Spotify token. Exiting Spotify analysis.")
        return []

    spotify_results = []
    # Spotify has a rate limit, a small delay is recommended
    SLEEP_TIME = 0.5 

    for video in video_data_list:
        title = video.get("title")
        channel_name = video.get("channel_name", "") # <-- EXTRACTING CHANNEL NAME
        
        print(f"Searching Spotify for: '{title}' by '{channel_name}'...")

        track_info = search_spotify(token, title, channel_name) # <-- PASSING CHANNEL NAME
        
        if track_info:
            combined_entry = {
                "youtube_video_id": video.get("video_id"),
                "youtube_title": title,
                "youtube_channel_name": channel_name,
                "spotify_data": track_info
            }
            spotify_results.append(combined_entry)
            print(f" -> Found: {track_info['name']} (Popularity: {track_info['popularity']})")
        else:
            print(f" -> Not found on Spotify.")
            
        time.sleep(SLEEP_TIME)

    # Save to JSON
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(spotify_results, f, indent=4, ensure_ascii=False)
        print(f"\nSpotify analysis saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving Spotify results to JSON: {e}")

    return spotify_results

if __name__ == "__main__":
    # This block is for standalone testing of spotify.py
    print("Running Spotify analysis standalone test...")
    example_data = [
        {"video_id": "vid1", "title": "Seggae man", "channel_name": "Ras Natty Baby Official"},
        {"video_id": "vid2", "title": "Zoli Fille (Official Video)", "channel_name": "Big Frankii"}
    ]
    run_spotify_analysis(example_data)