import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)      # Apollo root (where .env is)
OUTPUT_DIR = os.path.join(CURRENT_DIR, "output")  # transcripts inside processing/output

# Load .env from project root
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Config
TABLE_NAME = "lyrics"        # change to your table name
DELETE_AFTER_UPLOAD = False  # set True if you want to delete .txt after upload


def list_transcript_files():
    """
    List all .txt transcript files in OUTPUT_DIR.
    """
    if not os.path.exists(OUTPUT_DIR):
        print(f"Output folder does not exist: {OUTPUT_DIR}")
        return []

    files = []
    for name in os.listdir(OUTPUT_DIR):
        if not name.lower().endswith(".txt"):
            continue
        path = os.path.join(OUTPUT_DIR, name)
        if os.path.isfile(path):
            files.append(path)

    print(f"Found {len(files)} transcript files in {OUTPUT_DIR}.")
    return sorted(files)


def upload_transcript(video_id: str, transcript: str):
    """
    Insert or update a transcript row in Supabase.
    Assumes a 'lyrics' table with video_id + transcript columns.
    """
    data = {
        "video_id": video_id,
        "transcript": transcript,
    }

    response = (
        supabase.table(TABLE_NAME)
        .upsert(data, on_conflict="video_id")
        .execute()
    )

    if response.data:
        print(f"Uploaded transcript for {video_id} to table '{TABLE_NAME}'.")
    else:
        print(f"Upsert for {video_id} returned no data. Check RLS policies.")


def sync_transcripts_to_db():
    files = list_transcript_files()
    if not files:
        return

    for path in files:
        name = os.path.basename(path)
        video_id, _ = os.path.splitext(name)

        try:
            with open(path, "r", encoding="utf-8") as f:
                transcript = f.read().strip()

            if not transcript:
                print(f"Transcript file {name} is empty. Skipping.")
                continue

            upload_transcript(video_id, transcript)

            if DELETE_AFTER_UPLOAD:
                os.remove(path)
                print(f"Deleted local file {name} after successful upload.")

        except Exception as e:
            print(f"Error processing {name}: {e}")


def main():
    sync_transcripts_to_db()


if __name__ == "__main__":
    main()
