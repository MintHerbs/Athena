import math
import time
import concurrent.futures # --- Added for parallelism
# Assuming these modules exist and return lists of dictionaries
# from engine.spotify import run_spotify_analysis 
# from engine.deezer import run_deezer_analysis 

# Placeholder functions for demonstration since the actual files were not provided
def run_spotify_analysis(raw_video_data):
    # This would contain Spotify API logic
    return [{"youtube_video_id": v["video_id"], "spotify_data": {"popularity": 50}} for v in raw_video_data]

def run_deezer_analysis(raw_video_data):
    # This would contain Deezer API logic
    return [{"youtube_video_id": v["video_id"], "deezer_data": {"rank": 100000}} for v in raw_video_data]
# End of Placeholder functions

def calculate_popularity_score(youtube_views, streaming_count):
    try:
        views = int(youtube_views)
        streams = int(streaming_count)
    except ValueError:
        return 0.0

    # Avoid division by zero and handle edge cases
    if views == 0 and streams == 0:
        return 1.0 
    if views == 0 or streams == 0:
        return 0.0 
        
    score = min(views, streams) / max(views, streams)
    return score

def get_best_streaming_count(spotify_data, deezer_data):
    # Spotify popularity is 0-100, we approximate streams by * 1,000,000 for weighting
    spotify_count = int(spotify_data.get("popularity", 0)) * 1000000 
    deezer_count = int(deezer_data.get("rank", 0)) 
    
    if spotify_count > 0 and deezer_count > 0:
        return max(spotify_count, deezer_count), "Combined"
    elif spotify_count > 0:
        return spotify_count, "Spotify"
    elif deezer_count > 0:
        return deezer_count, "Deezer"
    else:
        return 0, "None"

def process_single_video_popularity(video, spotify_results, deezer_results):
    video_id = video["video_id"]
    youtube_views = video.get("views", "0") # <-- Data point 1 (NEW)

    spotify_match = next((item for item in spotify_results if item['youtube_video_id'] == video_id), None)
    deezer_match = next((item for item in deezer_results if item['youtube_video_id'] == video_id), None)
    
    spotify_data = spotify_match['spotify_data'] if spotify_match else {}
    deezer_data = deezer_match['deezer_data'] if deezer_match else {}

    best_streams, platform_used = get_best_streaming_count(spotify_data, deezer_data)
    normalized_score = calculate_popularity_score(youtube_views, best_streams) # <-- Data point 2 (NEW)
    final_score_flag = 1 if normalized_score >= 0.5 else 0
    
    return {
        "video_id": video_id,
        "youtube_views": youtube_views,
        "streaming_count_used": best_streams,
        "streaming_platform_used": platform_used, # <-- Data point 3 (NEW)
        "normalized_score": round(normalized_score, 4),
        "popularity_flag": final_score_flag
    }

def run_multiplatform_analysis(raw_video_data):
    """
    Orchestrates Spotify/Deezer analysis in PARALLEL and calculates scores.
    """
    print("\n--- Starting Multiplatform Analysis (Forking Processes) ---")

    # --- FORK PROCESSES HERE ---
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit both tasks to run simultaneously
        future_spotify = executor.submit(run_spotify_analysis, raw_video_data)
        future_deezer = executor.submit(run_deezer_analysis, raw_video_data)
        
        # Wait for results
        spotify_results = future_spotify.result()
        deezer_results = future_deezer.result()
    
    # Merge results
    final_popularity_data = []
    print("\nCalculating Final Popularity Scores...")
    for video in raw_video_data:
        # This function returns all the required data points
        score_data = process_single_video_popularity(video, spotify_results, deezer_results) 
        final_popularity_data.append(score_data)

    print(f"Calculated scores for {len(final_popularity_data)} videos.")
    return final_popularity_data