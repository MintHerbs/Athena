import os
import time
import re
import requests
import yaml
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY not found in .env. Please set it before running this script.")

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# How long to sleep between API calls (in seconds)
SLEEP_TIME = 0.2


def load_artists(filepath="artist.txt"):
    """
    Load artist names from a text file.
    Expects one artist name per line.
    """
    artists = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name:
                    artists.append(name)
    except FileNotFoundError:
        print(f"Error: {filepath} not found.")
    return artists


def score_channel_candidate(artist_name, channel_title, channel_description):
    """
    Assign a heuristic score to a channel candidate for the given artist.
    Higher score means more likely to be the "official" or main channel.
    """
    score = 0
    a = artist_name.lower()
    t = channel_title.lower()
    d = (channel_description or "").lower()

    # Artist name appearance in title or description
    if a in t:
        score += 4
    if a in d:
        score += 2

    # Exact or near exact match in title
    def normalize(s):
        return re.sub(r"[^a-z0-9]", "", s.lower())

    if normalize(artist_name) == normalize(channel_title):
        score += 5

    # Reward "official" (but not "topic")
    if "official" in t:
        score += 2

    # Penalise topic, tv, records etc (these are sometimes auto generated or label channels)
    penalty_words = ["topic", "tv", "records", "record", "label", "vevo"]
    for w in penalty_words:
        if w in t:
            score -= 2

    return score


def find_best_channel_for_artist(artist_name):
    """
    Use YouTube Data API v3 search endpoint to find the best channel candidate
    for a given artist name.

    Returns (channel_id, channel_title, channel_url) or (None, None, None).
    """
    params = {
        "key": API_KEY,
        "part": "snippet",
        "type": "channel",
        "q": artist_name,
        "maxResults": 5,
    }

    try:
        response = requests.get(YOUTUBE_SEARCH_URL, params=params)
        data = response.json()

        if data.get("error"):
            message = data["error"].get("message", "Unknown error")
            print(f"[API ERROR] {artist_name}: {message}")
            return None, None, None

        items = data.get("items", [])
        if not items:
            print(f"[NO RESULTS] No channels found for '{artist_name}'.")
            return None, None, None

        best_item = None
        best_score = float("-inf")

        for item in items:
            snippet = item.get("snippet", {})
            channel_title = snippet.get("title", "")
            channel_description = snippet.get("description", "")
            channel_id = item.get("snippet", {}).get("channelId") or item.get("id", {}).get("channelId")

            if not channel_id:
                continue

            s = score_channel_candidate(artist_name, channel_title, channel_description)
            # Uncomment if you want to see debug scoring
            # print(f"  Candidate: {channel_title} (score {s})")

            if s > best_score:
                best_score = s
                best_item = (channel_id, channel_title)

        if best_item is None:
            print(f"[NO VALID CANDIDATE] No suitable channel for '{artist_name}'.")
            return None, None, None

        channel_id, channel_title = best_item
        channel_url = f"https://www.youtube.com/channel/{channel_id}"

        print(f"[MATCH] '{artist_name}' -> {channel_title} ({channel_id})")
        return channel_id, channel_title, channel_url

    except requests.exceptions.RequestException as e:
        print(f"[CONNECTION ERROR] Failed to search for '{artist_name}': {e}")
        return None, None, None
    except Exception as e:
        print(f"[UNKNOWN ERROR] Unexpected error for '{artist_name}': {e}")
        return None, None, None


def generate_channels_yaml(channel_records, output_path="channels.yml"):
    """
    Write the discovered channels into a YAML file in the format:

    channels:
      - https://www.youtube.com/channel/UC... # Artist Name
    """
    data = {"channels": []}

    for rec in channel_records:
        artist_name = rec["artist_name"]
        channel_id = rec["channel_id"]
        channel_title = rec["channel_title"]

        url = f"https://www.youtube.com/channel/{channel_id}"
        comment = channel_title or artist_name
        # Store as plain url; comments are just for human reference
        data["channels"].append(f"{url}  # {comment}")

    # We want to keep the inline comment, so we write manually rather than letting
    # yaml.dump quote the whole string.
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Auto generated list of YouTube channels for Sega artists\n")
        f.write("channels:\n")
        for rec in channel_records:
            artist_name = rec["artist_name"]
            channel_id = rec["channel_id"]
            channel_title = rec["channel_title"]
            url = f"https://www.youtube.com/channel/{channel_id}"
            comment = channel_title or artist_name
            f.write(f"  - {url} # {comment}\n")

    print(f"\nWritten {len(channel_records)} channels to {output_path}.")


if __name__ == "__main__":
    artists = load_artists("artist.txt")
    if not artists:
        print("No artists found in artist.txt. Exiting.")
        raise SystemExit

    print(f"Found {len(artists)} artist names. Searching YouTube...")

    channel_records = []

    for artist in artists:
        print(f"\nSearching for: {artist}")
        channel_id, channel_title, channel_url = find_best_channel_for_artist(artist)

        if channel_id:
            channel_records.append(
                {
                    "artist_name": artist,
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                }
            )
        else:
            print(f"  -> Skipping '{artist}', no suitable channel found.")

        time.sleep(SLEEP_TIME)

    if channel_records:
        generate_channels_yaml(channel_records, "channels.yml")
    else:
        print("No channels were found for any artists.")
