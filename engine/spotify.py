import os
import requests
import json
import base64
import time
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
OUTPUT_FILE = "spotify_analysis_results.json"

if not CLIENT_ID or not CLIENT_SECRET:
    print("WARNING: Spotify credentials not found in .env. Skipping Spotify analysis.")
    SPOTIFY_ENABLED = False
else:
    SPOTIFY_ENABLED = True


# --- Helper functions for cleaning title and channel name ---


def clean_title_for_search(song_title: str) -> str:
    """
    Clean the YouTube video title to make it closer to a Spotify track name.

    Steps:
      - Keep only the part before the first '(' or '['
      - Remove common noise like 'Official Video', 'Clip Officiel', 'Lyrics'
      - Collapse extra whitespace and remove stray hyphens
    """
    t = song_title

    # Keep only part before first '(' or '['
    t = re.split(r"[\(\[]", t)[0]

    # Remove phrases like 'Official Video', 'Clip Officiel', 'Lyrics'
    t = re.sub(
        r"(?i)\b(official video|clip officiel|official audio|lyrics|lyric video|video clip|prod\.?|produced by)\b",
        "",
        t,
    )

    # Collapse multiple spaces and strip hyphens at ends
    t = re.sub(r"\s+", " ", t).strip(" -")
    return t.strip()


def clean_channel_name_for_search(channel_name: str) -> str:
    """
    Clean the YouTube channel name to look more like a Spotify artist name.

    Removes common suffixes like Official, Records, Topic, TV, Music, etc.
    """
    if not channel_name:
        return ""

    a = channel_name

    # Remove words that are usually not part of the artist name
    a = re.sub(
        r"(?i)\b(official|records?|topic|tv|channel|music|videos?)\b",
        "",
        a,
    )

    # Collapse spaces and strip hyphens
    a = re.sub(r"\s+", " ", a).strip(" -")
    return a.strip()


# --- Spotify API Functions ---


def get_spotify_token():
    """
    Retrieve an access token from the Spotify Accounts service.
    """
    if not SPOTIFY_ENABLED:
        return None

    auth_url = "https://accounts.spotify.com/api/token"
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    try:
        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status()
        json_data = response.json()
        return json_data.get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting Spotify token: {e}")
        return None


def search_spotify(token, song_title, channel_name):
    """
    Search Spotify for a track using the cleaned title and artist,
    with several fallback query strategies.
    """
    if not token:
        return None

    base_url = "https://api.spotify.com/v1/search"

    clean_title = clean_title_for_search(song_title)
    artist_guess = clean_channel_name_for_search(channel_name)

    headers = {"Authorization": f"Bearer {token}"}

    queries = []

    if artist_guess:
        # 1. Fielded search with track and artist
        queries.append(f'track:"{clean_title}" artist:"{artist_guess}"')
        # 2. Free text search combining both
        queries.append(f'"{clean_title}" "{artist_guess}"')

    # 3. Title only as last resort
    queries.append(f'"{clean_title}"')

    for q in queries:
        params = {
            "q": q,
            "type": "track",
            "limit": 1,
        }

        try:
            # Debug line if you want to inspect queries
            # print(f"    [SPOTIFY QUERY] {q}")
            response = requests.get(base_url, headers=headers, params=params)
            data = response.json()

            tracks = data.get("tracks", {}).get("items")
            if tracks:
                track = tracks[0]
                artist_name = (
                    track["artists"][0]["name"] if track["artists"] else "Unknown Artist"
                )
                return {
                    "spotify_id": track["id"],
                    "name": track["name"],
                    "artist": artist_name,
                    "popularity": track["popularity"],
                    "link": track["external_urls"]["spotify"],
                }
        except Exception as e:
            print(f"Error searching Spotify for '{q}': {e}")
            # Try next query

    # If all queries fail
    return None


def run_spotify_analysis(video_data_list):
    """
    Main function called by app.py.
    Takes a list of video dicts, finds them on Spotify, and saves results.

    Expects each video dict to have:
      - "video_id"
      - "title"
      - "channel_name"
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
    SLEEP_TIME = 0.5  # small delay to be gentle to the API

    for video in video_data_list:
        title = video.get("title")
        channel_name = video.get("channel_name", "")

        print(f"Searching Spotify for: '{title}' by '{channel_name}'...")

        track_info = search_spotify(token, title, channel_name)

        if track_info:
            combined_entry = {
                "youtube_video_id": video.get("video_id"),
                "youtube_title": title,
                "youtube_channel_name": channel_name,
                "spotify_data": track_info,
            }
            spotify_results.append(combined_entry)
            print(
                f" -> Found: {track_info['name']} by {track_info['artist']} "
                f"(Popularity: {track_info['popularity']})"
            )
        else:
            print(" -> Not found on Spotify.")

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
    # Standalone test
    print("Running Spotify analysis standalone test...")
    example_data = [
        {
            "video_id": "vid1",
            "title": "Zoli Fille - Big Frankii (Official Video)",
            "channel_name": "Big Frankii",
        },
        {
            "video_id": "vid2",
            "title": "Seggae man",
            "channel_name": "Ras Natty Baby Official",
        },
    ]
    run_spotify_analysis(example_data)
