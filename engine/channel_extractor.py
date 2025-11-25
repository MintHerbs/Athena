import yaml
import requests
import os
import re
from dotenv import load_dotenv

# --- Setup and Constants ---
load_dotenv()
# IMPORTANT: This script uses the GEMINI_API_KEY from your .env 
# for access to the Google YouTube Data API v3.
API_KEY = os.getenv("GEMINI_API_KEY") 

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please ensure it is set.")

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/channels"

def load_channel_urls(filepath="channels.yml"):
    """Loads the list of channel URLs from the YAML file."""
    print(f"Loading URLs from {filepath}...")
    try:
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('channels', [])
    except FileNotFoundError:
        print(f"Error: {filepath} not found. Please create it or ensure the path is correct.")
        return []
    except Exception as e:
        print(f"Error loading YAML: {e}")
        return []

def get_channel_id(url):
    """
    Extracts the channel ID (UC...) from a URL or looks it up via API based on the handle or username.
    
    Returns: (channel_id, channel_name)
    """
    print(f"\nProcessing URL: {url}")
    
    # --- 1. Attempt to extract ID directly from URL ---
    # Pattern: Standard /channel/UC... (24 character ID starting with UC)
    match_channel = re.search(r'/channel/([a-zA-Z0-9_-]{24})', url)
    if match_channel:
        channel_id = match_channel.group(1)
        # We'll use API to get the name later if we need it, but for now, we have the ID.
        print(f"  [EXTRACTED] Channel ID directly from URL: {channel_id}")
        return channel_id, channel_id 

    # --- 2. Extract handle/username for API Lookup ---
    
    # Handles @segamp3 format
    match_handle = re.search(r'@([a-zA-Z0-9_-]+)', url) 
    # Handles legacy /user/ channels
    match_user = re.search(r'/user/([a-zA-Z0-9_-]+)', url) 
    
    search_query = None
    if match_handle:
        search_query = match_handle.group(1)
        search_type = 'forHandle'
    elif match_user:
        search_query = match_user.group(1)
        search_type = 'forUsername'
    else:
        print(f"  [SKIPPED] Could not parse handle or ID from URL format. Skipping.")
        return None, None

    # --- 3. Make API Request ---
    params = {
        "key": API_KEY,
        "part": "snippet",
        search_type: search_query
    }
    
    try:
        response = requests.get(YOUTUBE_SEARCH_URL, params=params).json()
        
        if response.get("error"):
            message = response["error"]["message"]
            print(f"  [API ERROR] {message}. Check API Key Quota/Validity. URL: {url}")
            return None, None

        if response.get("items"):
            item = response["items"][0]
            channel_id = item["id"]
            channel_name = item["snippet"]["title"]
            print(f"  [FOUND VIA API] ID: {channel_id}, Name: {channel_name}")
            return channel_id, channel_name
        else:
            print(f"  [NOT FOUND] API returned no channel for query '{search_query}'.")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"  [CONNECTION ERROR] Failed to connect to YouTube API: {e}")
        return None, None
    except Exception as e:
        print(f"  [UNKNOWN ERROR] An unexpected error occurred: {e}")
        return None, None


def generate_output_file(id_list, output_filepath="config_channel_ids_output.txt"):
    """Writes the final list of IDs to a file."""
    if not id_list:
        print("\nNo channel IDs were successfully retrieved.")
        return

    content = "channel_ids:\n"
    for channel_id, channel_name in id_list:
        content += f'  - {channel_id} # {channel_name}\n'
    
    with open(output_filepath, 'w') as f:
        f.write(content)

    print(f"\n--- SUCCESS! ---")
    print(f"Output written to {output_filepath}.")
    print("\nCopy the content below and paste it into your main config.yml:")
    print("--------------------------------------------------------------------------------")
    print(content)
    print("--------------------------------------------------------------------------------")


if __name__ == "__main__":
    urls = load_channel_urls()
    final_ids = []
    
    if urls:
        print(f"Processing {len(urls)} channel URLs...")
        for url in urls:
            channel_id, channel_name = get_channel_id(url)
            # If we extracted the ID directly but don't have the name, try to look up the name
            if channel_id and channel_id == channel_name:
                # Basic check to see if the placeholder name is the ID itself
                try:
                    r = requests.get(YOUTUBE_SEARCH_URL, params={"key": API_KEY, "part": "snippet", "id": channel_id}).json()
                    if r.get("items"):
                        channel_name = r["items"][0]["snippet"]["title"]
                        print(f"  [NAME FOUND] Successfully retrieved channel name: {channel_name}")
                except:
                    # If API fails here, we stick with the ID as the name placeholder
                    pass

            if channel_id:
                final_ids.append((channel_id, channel_name))
        
        generate_output_file(final_ids)
    else:
        print("No URLs found in channels.yml to process.")