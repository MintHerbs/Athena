from dotenv import load_dotenv  # used to read .env file where API key is stored
import yaml          # used to read config.yml
import csv           # used for writing results to CSV files
import os            # used for file path handling
from tqdm import tqdm # used for progress bars while scraping
import requests      # used for calling YouTube API endpoints
import time          # used for adding delays between API calls

# --- CONFIGURATION & SETUP ---

# Load .env file first
load_dotenv()

# Read API key from environment
API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("Missing YOUTUBE_API_KEY in environment or .env file.")

# Opens and reads configuration settings from config.yml
with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# URL for retrieving channel information (includes uploads playlist ID)
CHANNELS_API_URL = "https://www.googleapis.com/youtube/v3/channels"

# URL for retrieving the videos inside a playlist (channel uploads)
PLAYLIST_API_URL = "https://www.googleapis.com/youtube/v3/playlistItems"

# URL for retrieving comments
COMMENTS_API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

# Output folder for CSV files
OUTPUT_FOLDER = config["output_folder"]
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# The set of fields that will appear as CSV columns
OUTPUT_FIELDS = ["video_id", "title", "comments"]

# List of channel IDs provided in config.yml
channel_ids = config["channel_ids"]

# --- HELPER FUNCTION ---

def process_video(video_snippet):
    # Creates a dictionary containing selected video information
    temp_dict = {}
    
    # Extracts the YouTube video ID
    # We assign this to a variable first so we can use it in comment_params below
    video_id = video_snippet["resourceId"]["videoId"]
    temp_dict["video_id"] = video_id
    
    # Extracts the video title
    temp_dict["title"] = video_snippet["title"]
    
    # 2. Fetch Comments for this specific video
    comment_params = {
        "key": API_KEY,
        "part": "snippet",
        "videoId": video_id, 
        "maxResults": 100, # The max allowed per page
        "textFormat": "plainText",
        "order": "relevance" 
    }

    try:
        # Make the API call
        r = requests.get(COMMENTS_API_URL, params=comment_params).json()
        
        # Check if comments exist and extracting them
        comment_list = []
        if "items" in r:
            for item in r["items"]:
                # Extract the actual comment text
                comment_text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                # Clean up newlines so they don't break the CSV format
                clean_comment = comment_text.replace("\n", " ").replace("\r", "")
                comment_list.append(clean_comment)
        
        # Join all 100 comments into one big string separated by a pipe symbol "|"
        temp_dict["comments"] = " | ".join(comment_list)
        
    except Exception as e:
        # This usually happens if comments are disabled on the video
        temp_dict["comments"] = "COMMENTS_DISABLED_OR_ERROR"

    return temp_dict

# --- MAIN EXECUTION LOOP ---

# Base parameters for the channels API call
channels_params = {
    "key": API_KEY,            
    "part": "contentDetails",  
}

# Base parameters for retrieving playlist items (videos)
playlist_params = {
    "key": API_KEY,      
    "part": "snippet",   
    "maxResults": 50,    
}

# Iterate over every channel ID in the config file
for channel_id in channel_ids:

    # Add or update the channel ID parameter in the request
    channels_params.update({"id": channel_id})

    # Request channel data from YouTube
    r = requests.get(
        CHANNELS_API_URL,
        params=channels_params,
    ).json()

    # Extract the ID of the uploads playlist for this channel
    if "items" not in r or not r["items"]:
        print(f"Skipping channel ID {channel_id} (Not found or no items)")
        continue
        
    uploads_id = r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Insert the playlist ID into the playlist query parameters
    playlist_params.update({"playlistId": uploads_id})

    # Request the first page of videos from the uploads playlist
    r = requests.get(
        PLAYLIST_API_URL,
        params=playlist_params,
    ).json()

    # Only continue if the response contains videos
    if "items" in r:

        # Extract channel name for naming the CSV file
        channel_name = r["items"][0]["snippet"]["channelTitle"]

        # Get token for next page of results, if present
        pageToken = r.get("nextPageToken")

        # Inform user which channel is being scraped
        print(f"Scraping {channel_name}'s videos:")

        # Create a progress bar based on total results available
        pbar = tqdm(total=r["pageInfo"]["totalResults"])

        # Prepare CSV file for writing results
        with open(
            os.path.join(OUTPUT_FOLDER, f"{channel_name}.csv".replace(os.sep, "_")),
            "w",
            encoding="utf-8-sig", 
        ) as f:

            # Create a CSV writer with the selected field names
            w = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)

            # Write header row to CSV
            w.writeheader()

            # Process the first batch of videos already retrieved
            for video in r["items"]:
                w.writerow(process_video(video["snippet"]))

            # Update progress bar for this first batch
            pbar.update(len(r["items"]))

            # Loop through next pages until no nextPageToken exists
            while pageToken:

                # Add next page token to request parameters
                playlist_params.update({"pageToken": pageToken})

                # Request the next page of videos
                r = requests.get(
                    PLAYLIST_API_URL,
                    params=playlist_params,
                ).json()

                # Write each video from the new page into the CSV file
                for video in r["items"]:
                    w.writerow(process_video(video["snippet"]))

                # Update progress bar by number of items processed
                pbar.update(len(r["items"]))

                # Retrieve next page token for further pagination
                pageToken = r.get("nextPageToken")

                # Small delay to avoid hammering YouTube API
                time.sleep(0.1)

        # Close the progress bar after finishing the channel
        pbar.close()

        # Reset pageToken parameter so it does not affect next channel
        playlist_params.update({"pageToken": None})