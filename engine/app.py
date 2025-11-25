import yaml
import os
from engine.scraper import run_scraper
from engine.gemini import run_gemini_processing
from engine.multiplatform_analysis import run_multiplatform_analysis
from database import insert_analysis_results

def load_config():
    """Loads configuration settings from config.yml."""
    try:
        with open('config.yml', 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print("Error: config.yml not found.")
        return None

def merge_results(gemini_data, multiplatform_data):
    """
    Merges the Gemini analysis (sentiment, genre) with the Multiplatform analysis (flags, scores) 
    using 'video_id' as the key.
    """
    merged_map = {item['video_id']: {} for item in gemini_data}

    # 1. Populate map with Gemini data (contains most of the required fields)
    for item in gemini_data:
        video_id = item['video_id']
        merged_map[video_id].update(item)
    
    # 2. Merge Multiplatform data (contains new scores/flags)
    for item in multiplatform_data:
        video_id = item['video_id']
        if video_id in merged_map:
            # Multiplatform data includes: 
            # normalized_score, streaming_platform_used, youtube_views, popularity_flag
            merged_map[video_id].update(item)
    
    # Return the final list of merged dictionaries
    final_list = list(merged_map.values())
    print(f"Successfully merged {len(final_list)} video analysis records.")
    return final_list

def main():
    config = load_config()
    if not config:
        return

    # --- Step 1: Fetching Data from YouTube ---
    print("Step 1: Fetching data from YouTube...")
    raw_video_data = run_scraper(config.get("channel_ids", []), config.get("output_folder", "data"))
    
    if not raw_video_data:
        print("No data scraped. Exiting application.")
        return

    # --- Step 2: Running Gemini Analysis (Sentiment, Genre) ---
    print("\nStep 2: Running Gemini Analysis...")
    gemini_analysis_results = run_gemini_processing(raw_video_data)

    # --- Step 3: Running Multiplatform Analysis (Popularity Score) ---
    print("\nStep 3: Running Multiplatform Analysis...")
    multiplatform_analysis_results = run_multiplatform_analysis(raw_video_data)
    
    # --- Step 4: Merge Results ---
    print("\nStep 4: Merging all analysis results...")
    final_merged_data = merge_results(gemini_analysis_results, multiplatform_analysis_results)

    # --- Step 5: Database Insertion (Supabase) ---
    print("\nStep 5: Inserting data into Supabase...")
    inserted_count = insert_analysis_results(final_merged_data)
    
    print(f"\n--- Process Complete ---")
    print(f"Total records analyzed: {len(final_merged_data)}")
    print(f"Total records inserted into Supabase: {inserted_count}")

if __name__ == "__main__":
    main()