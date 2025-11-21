import yaml          # used to read config.yml
import csv           # used for writing results to CSV files
import os            # used for file path handling
from tqdm import tqdm # used for progress bars while scraping
import requests      # used for calling YouTube API endpoints
import time          # used for adding delays between API calls


def process_video(video_snippet):
    # Creates a dictionary containing selected video information
    temp_dict = {}
    # Extracts the YouTube video ID
    temp_dict["video_id"] = video_snippet["resourceId"]["videoId"]
    # Extracts the video title
    temp_dict["title"] = video_snippet["title"]
    # Extracts the publish date of the video
    temp_dict["video_published_at"] = video_snippet["publishedAt"]
    # Returns the cleaned and formatted video data
    return temp_dict


# Opens and reads configuration settings from config.yml
with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Extract API key from configuration file
API_KEY = config["API_KEY"]

# URL for retrieving channel information (includes uploads playlist ID)
CHANNELS_API_URL = "https://www.googleapis.com/youtube/v3/channels"

# URL for retrieving the videos inside a playlist (channel uploads)
PLAYLIST_API_URL = "https://www.googleapis.com/youtube/v3/playlistItems"

# Output folder for CSV files
OUTPUT_FOLDER = config["output_folder"]

# The set of fields that will appear as CSV columns
OUTPUT_FIELDS = ["video_id", "title", "video_published_at"]

# List of channel IDs provided in config.yml
channel_ids = config["channel_ids"]

# Base parameters for the channels API call
channels_params = {
    "key": API_KEY,            # YouTube API key
    "part": "contentDetails",  # We need contentDetails to get the uploads playlist ID
}

# Base parameters for retrieving playlist items (videos)
playlist_params = {
    "key": API_KEY,      # API key again
    "part": "snippet",   # snippet gives title and metadata
    "maxResults": 50,    # maximum allowed per request by YouTube API
}

# Iterate over every channel ID in the config file
for channel_id in channel_ids:

    # Add or update the channel ID parameter in the request
    channels_params.update({"id": channel_id})

    # Request channel data from YouTube, then parse JSON response
    r = requests.get(
        CHANNELS_API_URL,
        params=channels_params,
    ).json()

    # Extract the ID of the uploads playlist for this channel
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
            encoding="utf-8",
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
