import os
import time
import sys
from yt_dlp import YoutubeDL

# --- Fix 1: Correct Relative Import ---
# Since database.py is a sibling in the 'engine' folder, use a relative import.
try:
    from .database import supabase
except ImportError:
    # Fallback/Safety net if running the file directly without Python -m command
    print("Warning: Using fallback import path. Ensure you run as a module or from project root.")
    # You may need to replace 'database' with 'engine.database' depending on your run method
    from database import supabase 


# --- Fix 2: Correct Audio Directory Path ---
# os.pardir is '..', so this resolves to: root/processing/audio
AUDIO_DIR = os.path.join(os.pardir, "processing", "audio")

# --- Throttling / safety knobs ---
MAX_DOWNLOADS_PER_RUN = 100     # hard cap per run (adjust as you like)
SLEEP_BETWEEN_DOWNLOADS = 5.0   # seconds to sleep after each download


def ensure_audio_folder():
    """
    Create the 'audio' folder if it does not exist, using the corrected path.
    """
    absolute_audio_path = os.path.abspath(AUDIO_DIR)
    
    if not os.path.exists(absolute_audio_path):
        os.makedirs(absolute_audio_path)
        print(f"Created folder: {absolute_audio_path}")
    else:
        print(f"Target folder exists: {absolute_audio_path}")


def get_target_videos():
    """
    Fetch all video_id values from Supabase where:
      - sentiment_flag = 1
      - sega_genre is not 'Not Sega'
    """
    print("Querying Supabase for target videos...")

    # NOTE: The Supabase table name must match exactly.
    response = (
        supabase.table("analysis")
        .select("video_id, sentiment_flag, sega_genre")
        .eq("sentiment_flag", 1)
        .neq("sega_genre", "Not Sega")
        .execute()
    )

    data = response.data or []
    print(f"Found {len(data)} videos that match the criteria.")
    return data


def download_audio_for_video(video_id: str):
    """
    Download YouTube audio for a single video_id and save as audio/<video_id>.mp3.
    Uses yt-dlp and ffmpeg for conversion.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    output_template = os.path.join(AUDIO_DIR, f"{video_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": False,
    }

    print(f"Downloading audio for {video_id} from {video_url} ...")

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    print(f"Finished: {os.path.join(AUDIO_DIR, video_id + '.mp3')}")



def main():
    ensure_audio_folder()

    videos = get_target_videos()
    downloaded_this_run = 0

    for row in videos:
        if downloaded_this_run >= MAX_DOWNLOADS_PER_RUN:
            print(
                f"\nReached MAX_DOWNLOADS_PER_RUN = {MAX_DOWNLOADS_PER_RUN}. "
                "Stop now and run the script again later if you need more."
            )
            break

        video_id = row.get("video_id")
        if not video_id:
            continue

        target_path = os.path.join(os.path.abspath(AUDIO_DIR), f"{video_id}.mp3")
        if os.path.exists(target_path):
            print(f"Skipping {video_id} - file already exists.")
            continue

        try:
            download_audio_for_video(video_id)
            downloaded_this_run += 1

            # polite delay between downloads
            print(f"Sleeping {SLEEP_BETWEEN_DOWNLOADS} seconds...")
            time.sleep(SLEEP_BETWEEN_DOWNLOADS)

        except Exception as e:
            msg = str(e)
            print(f"Error downloading {video_id}: {msg}")

            # If YouTube starts complaining about too many requests, stop the run
            if "429" in msg or "Too Many Requests" in msg:
                print(
                    "\nIt looks like YouTube is rate limiting you "
                    "(HTTP 429 / Too Many Requests). "
                    "Stopping this run. Try again later with fewer downloads."
                )
                break


if __name__ == "__main__":
    main()