import requests
import json
import os
import time

# --- Configuration ---
OUTPUT_FILE = "deezer_analysis_results.json"

# --- Deezer API Functions ---

def search_track(song_title, channel_name):
    """
    Searches for a track on Deezer by combining the video title and channel name.
    """
    base_url = "https://api.deezer.com/search/track"
    
    # Clean the title (e.g., removing text in parentheses)
    clean_title = song_title.split("(")[0].strip()
    
    # Combine title and channel name for a more targeted search query (e.g., "title artist")
    search_query = f"{clean_title} {channel_name}" # <-- USING CHANNEL NAME
    
    # Parameters for the search: query and limit to 1 result (the best match)
    params = {"q": search_query, "limit": 1}
    
    try:
        response = requests.get(base_url, params=params).json()
        
        if response.get("data"):
            track = response["data"][0]  # best match
            
            # Deezer's 'rank' field is a useful measure of popularity/relevance
            return {
                "deezer_id": track.get("id"),
                "name": track.get("title"),
                "artist": track.get("artist", {}).get("name"),
                "rank": track.get("rank"),
                "link": track.get("link")
            }
        else:
            return None
    except Exception as e:
        print(f"Error searching Deezer for '{search_query}': {e}")
        return None

def run_deezer_analysis(video_data_list):
    """
    Main function called by app.py.
    Takes a list of video dicts (from scraper), finds them on Deezer,
    and saves the results to a JSON file.
    """
    print("\n--- Starting Deezer Analysis ---")

    deezer_results = []
    
    # We use a rate-limiting sleep here to be polite to the Deezer API
    SLEEP_TIME = 0.5 

    for video in video_data_list:
        title = video.get("title")
        channel_name = video.get("channel_name", "") # <-- EXTRACTING CHANNEL NAME
        
        print(f"Searching Deezer for: '{title}' by '{channel_name}'...")

        # --- UPDATED CALL: Pass both title and channel_name ---
        track_info = search_track(title, channel_name)
        
        if track_info:
            # Combine the YouTube video details with the Deezer Data
            combined_entry = {
                "youtube_video_id": video.get("video_id"),
                "youtube_title": title,
                "youtube_channel_name": channel_name, # Also add to the output JSON
                "deezer_data": track_info
            }
            deezer_results.append(combined_entry)
            print(f" -> Found: {track_info['name']} by {track_info['artist']} (Rank: {track_info['rank']})")
        else:
            print(f" -> Not found on Deezer.")
            
        time.sleep(SLEEP_TIME)

    # Save to JSON as requested
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(deezer_results, f, indent=4, ensure_ascii=False)
        print(f"\nDeezer analysis saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving Deezer results to JSON: {e}")

    return deezer_results

if __name__ == "__main__":
    # This block is for standalone testing of deezer.py
    print("Running Deezer analysis standalone test...")
    example_data = [
        {"video_id": "vid1", "title": "Seggae man", "channel_name": "Ras Natty Baby Official"},
        {"video_id": "vid2", "title": "Zoli Fille - Big Frankii (Official Video)", "channel_name": "Big Frankii"}
    ]
    run_deezer_analysis(example_data)