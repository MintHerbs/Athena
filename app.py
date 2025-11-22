import csv
import os
from scraper import run_scraper
from gemini import run_gemini_processing

def main():
    # 1. Run the Scraper
    # This grabs the data in memory (no CSV creation in this step)
    print("Step 1: Fetching data from YouTube...")
    raw_video_data = run_scraper()
    
    if not raw_video_data:
        print("No data scraped. Exiting.")
        return

    # 2. Run Gemini
    # Pass the raw data directly to the Gemini module
    print("Step 2: Sending data to Gemini for analysis...")
    analyzed_data = run_gemini_processing(raw_video_data)

    # 3. Save Final Output
    # Now we save the final combined result to a CSV
    output_filename = "final_analysis_results.csv"
    
    print(f"Step 3: Saving results to {output_filename}...")
    
    # Define the columns (Make sure these match the keys in your dictionaries)
    fieldnames = ["video_id", "sentiment_flag", "emotional_genre", "sega_genre"]
    
    with open(output_filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(analyzed_data)

    print("Done! Application finished successfully.")

if __name__ == "__main__":
    main()