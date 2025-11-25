import os
import json
import time
from dotenv import load_dotenv
from google import genai
from tqdm import tqdm

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env file")

client = genai.Client(api_key=GEMINI_KEY)

def analyze_single_video(video_id, title, comments):
    """
    Sends a single video's data to Gemini for sentiment/genre analysis and 
    confidence scoring.
    """
    prompt = f"""
    You are an expert cultural analyst of Mauritian Sega music.
    
    Video Title: "{title}"
    Comments: "{comments}"
    
    Task:
    1. Read the comments. If >50% of the comments are about how the music made them feel, explaining their emotions, or sharing personal stories (as opposed to just "nice song" or visual comments), set 'sentiment_flag' to 1. Otherwise 0.
    2. Identify the specific 'emotional_genre' evoked (e.g., Happiness, Nostalgia, Depression, Party, Sadness).
    
    # --- ADJUSTMENTS START HERE ---
    3. Based on the Video Title and comments:
       a. If the content is clearly **not** Sega music (e.g., the language is irrelevant, the comments discuss non-Sega genres like Hip Hop or Rock, or the title implies unrelated content), set 'sega_genre' to **"Not Sega"**.
       b. If the content is Sega music, you **must** pick one of the specific 'sega_genre' categories: **Political Sega, Chagos Sega, Fancy Sega, or Roots Sega**. Do NOT use "Unknown". Force a choice based on the best fit.
       
    # --- ADJUSTMENTS END HERE ---
    
    4. Assess the overall volume and detail of the provided comments. Set 'comment_density_rating' to one of three values: 'Low' (few, short, generic comments), 'Medium' (moderate volume, some detail), or 'High' (many, detailed, story-driven comments).
    5. Provide a 'gemini_confidence_score' between 0.0 (low confidence) and 1.0 (high confidence) for the analysis, based on how clear and consistent the title and comments were in determining the genres.

    Return pure JSON format:
    {{
        "video_id": "{video_id}",
        "sentiment_flag": 0 or 1,
        "emotional_genre": "string",
        "sega_genre": "string",
        "gemini_confidence_score": 0.0 to 1.0,
        "comment_density_rating": "Low", "Medium", or "High"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config={
                "response_mime_type": "application/json"
            }
        )
        
        # Parse the JSON string
        data = json.loads(response.text)

        # Handle case where Gemini returned a list [ {...} ] instead of a dict {...}
        if isinstance(data, list):
            if len(data) > 0:
                return data[0]
            # If list is empty, return error structure with new fields
            else:
                return { 
                    "video_id": video_id,
                    "sentiment_flag": 0,
                    "emotional_genre": "Error",
                    "sega_genre": "Not Sega", # Fallback for error handling
                    "gemini_confidence_score": 0.0,
                    "comment_density_rating": "Low"
                }
        
        # Check if the required keys exist before returning
        if data.get("sega_genre") == "Unknown" or not data.get("sega_genre"):
            # This is an extra safety check in case the model ignores the prompt
            # If it still returns unknown, we force it to the most common default
            data["sega_genre"] = "Roots Sega"
            
        return data

    except Exception as e:
        print(f"Error analyzing {video_id}: {e}")
        return {
            "video_id": video_id,
            "sentiment_flag": 0,
            "emotional_genre": "Error",
            "sega_genre": "Not Sega", # Use "Not Sega" as the default genre for hard crashes
            "gemini_confidence_score": 0.0,
            "comment_density_rating": "Low"
        }

def run_gemini_processing(scraped_data):
    """
    Iterates through the list of scraped data and applies Gemini analysis.
    """
    print(f"\n--- Starting Gemini Analysis on {len(scraped_data)} videos ---")
    
    final_results = []
    
    # Using tqdm to show a progress bar for the analysis phase
    for video in tqdm(scraped_data, desc="Analyzing Sentiment"):
        analysis = analyze_single_video(
            video["video_id"], 
            video["title"], 
            video["comments"]
        )
        
        # Combine original data with analysis if needed, or just store analysis
        final_results.append(analysis)
        
        # Sleep to avoid hitting Gemini rate limits (15 requests per minute on free tier)
        time.sleep(4) 
        
    return final_results