import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# --- Supabase Keys ---
# Using SUPABASE_URL and SUPABASE_KEY as set in your .env
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file. Please check your .env configuration.")

# Initialize the Supabase client
supabase: Client = create_client(url, key)

def insert_analysis_results(data_list):
    """
    Takes the final list of merged dictionaries from app.py and inserts them 
    into the Supabase 'analysis' table.
    
    This function handles the required renaming:
    - popularity_flag (Python) -> multianalysis_flag (SQL)
    """
    if not data_list:
        print("No data to insert.")
        return 0

    # 1. Prepare data payload matching SQL Column Names
    records_to_insert = []
    
    for item in data_list:
        try:
            # We map Python dictionary keys to your Supabase SQL column names
            record = {
                "video_id": item.get("video_id"),
                "sentiment_flag": item.get("sentiment_flag", 0),
                
                # MAPPING: Python uses 'popularity_flag', SQL uses 'multianalysis_flag'
                "multianalysis_flag": item.get("popularity_flag", 0), 
                
                "emotional_genre": item.get("emotional_genre", "Unknown"),
                "sega_genre": item.get("sega_genre", "Not Sega"),
                "gemini_confidence_score": float(item.get("gemini_confidence_score", 0.0)),
                "comment_density_rating": item.get("comment_density_rating", "Low"),
                
                # --- NEW COLUMNS ADDED HERE ---
                "normalized_score": float(item.get("normalized_score", 0.0)),
                "streaming_platform_used": item.get("streaming_platform_used", "None"),
                "youtube_views": int(item.get("youtube_views", 0))
            }
            records_to_insert.append(record)
        except Exception as e:
            print(f"Skipping record due to data conversion error: {e}. Data: {item}")
            continue

    try:
        print(f"Attempting to insert {len(records_to_insert)} records into Supabase...")
        
        # 2. Perform the Insert
        # .insert() handles batch insertion automatically
        response = supabase.table("analysis").insert(records_to_insert).execute()
        
        # 3. Check success
        if response.data:
            print(f"✅ Supabase Insert Success! Inserted {len(response.data)} rows.")
            return len(response.data)
        else:
            print("⚠️ Insert ran, but no data returned. Check your Supabase RLS policies if using the 'Anon' key.")
            return 0

    except Exception as e:
        print(f"❌ Error inserting into Supabase: {e}")
        return 0