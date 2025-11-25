import math
import time
import concurrent.futures # --- Added for parallelism
from spotify import run_spotify_analysis
from deezer import run_deezer_analysis 

def calculate_popularity_score(youtube_views, streaming_count):
    try:
        views = int(youtube_views)
        streams = int(streaming_count)
    except ValueError:
        return 0.0

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
    youtube_views = video.get("views", "0")

    spotify_match = next((item for item in spotify_results if item['youtube_video_id'] == video_id), None)
    deezer_match = next((item for item in deezer_results if item['youtube_video_id'] == video_id), None)
    
    spotify_data = spotify_match['spotify_data'] if spotify_match else {}
    deezer_data = deezer_match['deezer_data'] if deezer_match else {}

    best_streams, platform_used = get_best_streaming_count(spotify_data, deezer_data)
    normalized_score = calculate_popularity_score(youtube_views, best_streams)
    final_score_flag = 1 if normalized_score >= 0.5 else 0
    
    return {
        "video_id": video_id,
        "youtube_views": youtube_views,
        "streaming_count_used": best_streams,
        "streaming_platform_used": platform_used,
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
        score_data = process_single_video_popularity(video, spotify_results, deezer_results)
        final_popularity_data.append(score_data)

    print(f"Calculated scores for {len(final_popularity_data)} videos.")
    return final_popularity_data