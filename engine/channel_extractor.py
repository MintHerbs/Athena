import yaml
import requests
import os
import re
from dotenv import load_dotenv

# --- Setup and Constants ---
load_dotenv()

# YouTube API key is not strictly needed in this version.
# We will resolve handles by scraping the channel page HTML.
# Keeping this here in case you want to extend it later.
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

USER_AGENT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}


def load_channel_urls(filepath="channels.yml"):
    """
    Load a list of channel URLs from a YAML file.

    Expects:
      channels:
        - https://www.youtube.com/@segamp3
        - https://www.youtube.com/channel/UC...

    If the YAML structure is broken, falls back to extracting every http URL
    from the file with a regex.
    """
    print(f"Loading URLs from {filepath}...")
    urls = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"YAML parse failed: {e}")
                config = None

        # Normal path - list under "channels"
        if isinstance(config, dict) and isinstance(config.get("channels"), list):
            for entry in config["channels"]:
                if entry:
                    urls.append(str(entry).strip())
        else:
            # Fallback - scan file for any http or https urls
            print("Could not find a valid 'channels' list, falling back to line based parsing...")
            with open(filepath, "r", encoding="utf-8") as f2:
                for line in f2:
                    match = re.search(r"https?://\S+", line)
                    if match:
                        urls.append(match.group(0))

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)

        print(f"Loaded {len(unique_urls)} unique URLs.")
        return unique_urls

    except FileNotFoundError:
        print(f"Error: {filepath} not found. Please create it or ensure the path is correct.")
        return []
    except Exception as e:
        print(f"Error loading channel URLs: {e}")
        return []


def extract_channel_id_from_html(html):
    """
    Try to extract a UC... channel ID from a YouTube channel page HTML.
    """
    # Pattern often appears as "channelId":"UCxxxxxxxxxxxxxxxxxxxxxx"
    m = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', html)
    if m:
        return m.group(1)

    # Fallback: YouTube sometimes uses "browseId":"UC..."
    m = re.search(r'"browseId":"(UC[0-9A-Za-z_-]{22})"', html)
    if m:
        return m.group(1)

    return None


def extract_channel_name_from_html(html):
    """
    Best effort: read <title> from the HTML as the channel name.
    It is not perfect but good enough for annotating the output file.
    """
    m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not m:
        return None

    title = m.group(1)
    # Clean common suffix like " - YouTube"
    title = re.sub(r"\s*-+\s*YouTube\s*$", "", title).strip()
    return title or None


def get_channel_id(url):
    """
    Extract the channel ID (UC...) from a URL.

    Strategy:
      1. If the URL already has /channel/UC..., extract and return it.
      2. Otherwise, request the channel page and parse the HTML for UC id.
    """
    print(f"\nProcessing URL: {url}")

    # 1. Try to extract UC id directly: /channel/UCxxxx...
    match_channel = re.search(r"/channel/(UC[0-9A-Za-z_-]{22})", url)
    if match_channel:
        channel_id = match_channel.group(1)
        print(f"  [EXTRACTED] Channel ID directly from URL: {channel_id}")
        # We will try to get a nicer name below by scraping HTML
        # so we still fall through to HTML fetch to get the name
        # but we already know the id
        known_id = channel_id
    else:
        known_id = None

    # If we do not know the id yet or we want the name, fetch HTML
    try:
        resp = requests.get(url, headers=USER_AGENT_HEADERS, timeout=10)
        resp.raise_for_status()
        html = resp.text
    except requests.exceptions.RequestException as e:
        print(f"  [CONNECTION ERROR] Failed to load page HTML: {e}")
        # If we at least know the id from the URL, return it with that as name
        if known_id:
            return known_id, known_id
        return None, None

    # If id was not in URL, try to extract from HTML
    channel_id = known_id or extract_channel_id_from_html(html)
    if not channel_id:
        print("  [NOT FOUND] Could not find UC channel id in HTML.")
        return None, None

    # Try to grab a nicer channel name from HTML title
    channel_name = extract_channel_name_from_html(html) or channel_id

    print(f"  [RESOLVED] ID: {channel_id}, Name: {channel_name}")
    return channel_id, channel_name


def generate_output_file(id_list, output_filepath="config_channel_ids_output.txt"):
    """Write the final list of IDs to a file."""
    if not id_list:
        print("\nNo channel IDs were successfully retrieved.")
        return

    content = "channel_ids:\n"
    for channel_id, channel_name in id_list:
        content += f"  - {channel_id} # {channel_name}\n"

    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("\n--- SUCCESS ---")
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

            if channel_id:
                final_ids.append((channel_id, channel_name))

        generate_output_file(final_ids)
    else:
        print("No URLs found in channels.yml to process.")
