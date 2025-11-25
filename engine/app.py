import concurrent.futures
from tabulate import tabulate

from scraper import run_scraper
from gemini import run_gemini_processing
from multiplatform_analysis import run_multiplatform_analysis
from database import insert_analysis_results


def merge_data(raw_data, gemini_data, multi_data):
    """
    Merge raw scraper data, Gemini analysis, and multiplatform scores
    into a single list of dictionaries based on video_id.
    """
    merged_list = []

    # Convert lists to dicts keyed by video_id for easy lookup
    gemini_dict = {item["video_id"]: item for item in gemini_data}
    multi_dict = {item["video_id"]: item for item in multi_data}

    for video in raw_data:
        vid_id = video["video_id"]
        g_data = gemini_dict.get(vid_id, {})
        m_data = multi_dict.get(vid_id, {})

        merged_entry = {
            **video,   # Scraper data
            **g_data,  # Gemini data
            **m_data,  # Multiplatform data
        }
        merged_list.append(merged_entry)

    return merged_list


def display_terminal_table(final_data):
    """
    Display data in the terminal as a formatted table.
    """
    table_data = []
    headers = [
        "Video URL",
        "Channel URL",
        "Sentiment Flag",
        "Multiplatform Flag",
        "Sega Genre",
        "Emotional Genre",
        "Comment Density",
        "Gemini Conf.",
    ]

    for item in final_data:
        row = [
            item.get("video_url", "N/A"),
            item.get("channel_url", "N/A"),
            item.get("sentiment_flag", 0),
            item.get("popularity_flag", 0),
            item.get("sega_genre", "N/A"),
            item.get("emotional_genre", "N/A"),
            item.get("comment_density_rating", "N/A"),
            item.get("gemini_confidence_score", 0.0),
        ]
        table_data.append(row)

    print("\n" + "=" * 50)
    print("FINAL ANALYSIS RESULTS")
    print("=" * 50)
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def main():
    # 1. Run the scraper
    print("Step 1: Fetching data from YouTube...")
    raw_video_data = run_scraper()

    if not raw_video_data:
        print("No data scraped. Exiting.")
        return

    # 2. Run Gemini and multiplatform analysis in parallel
    print("\nStep 2: Launching Parallel Processes (Gemini and Multiplatform)...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_gemini = executor.submit(run_gemini_processing, raw_video_data)
        future_multi = executor.submit(run_multiplatform_analysis, raw_video_data)

        gemini_results = future_gemini.result()
        multiplatform_results = future_multi.result()

    # 3. Merge results
    print("\nStep 3: Merging Data...")
    final_analyzed_data = merge_data(raw_video_data, gemini_results, multiplatform_results)

    # 4. Display summary table
    display_terminal_table(final_analyzed_data)

    # 5. Save to Supabase
    print("\nStep 4: Saving results to Supabase...")
    inserted_count = insert_analysis_results(final_analyzed_data)

    if inserted_count > 0:
        print(f"Done. {inserted_count} records saved to Supabase.")
    else:
        print("Application finished, but no records were saved.")


if __name__ == "__main__":
    main()
