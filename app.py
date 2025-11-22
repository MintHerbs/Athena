# --- Remove: import csv ---
# --- Remove: from scraper import run_scraper ---
from scraper import run_scraper
from gemini import run_gemini_processing
from database import insert_analysis_results # --- ADD THIS ---

def main():
    # 1. Run the Scraper
    print("Step 1: Fetching data from YouTube...")
    raw_video_data = run_scraper()
    
    if not raw_video_data:
        print("No data scraped. Exiting.")
        return

    # 2. Run Gemini
    print("Step 2: Sending data to Gemini for analysis...")
    analyzed_data = run_gemini_processing(raw_video_data)

    # 3. Save Final Output (to MongoDB instead of CSV)
    
    print("Step 3: Saving results to MongoDB Atlas (apollo.gemini_analysis)...")
    
    # --- Replace CSV logic with DB insertion ---
    inserted_count = insert_analysis_results(analyzed_data)

    if inserted_count > 0:
        print(f"Done! Application finished successfully. {inserted_count} records saved to MongoDB.")
    else:
        print("Application finished, but no records were saved to the database.")

if __name__ == "__main__":
    main()