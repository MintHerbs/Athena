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
    Sends a single video's data to Gemini for sentiment/genre analysis.
    """
    prompt = f"""
    You are an expert cultural analyst of Mauritian Sega music.
    
    Video Title: "{title}"
    Comments: "{comments}"
    
    Task:
    1. Read the comments. If >50% of the comments are about how the music made them feel, explaining their emotions, or sharing personal stories (as opposed to just "nice song" or visual comments), set 'sentiment_flag' to 1. Otherwise 0.
    2. Identify the specific 'emotional_genre' evoked (e.g., Happiness, Nostalgia, Depression, Party, Sadness).
    3. Based on the Title, identify the 'sega_genre' (e.g., Political Sega, Chagos Sega, Fancy Sega, Roots Sega).
    
    Return pure JSON format:
    {{
        "video_id": "{video_id}",
        "sentiment_flag": 0 or 1,
        "emotional_genre": "string",
        "sega_genre": "string"
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

        # ---------------------------------------------------------
        # THE FIX: Check if Gemini returned a list [ {...} ] 
        # instead of a dict {...}
        # ---------------------------------------------------------
        if isinstance(data, list):
            if len(data) > 0:
                return data[0] # Extract the dictionary from the list
            else:
                return { # Handle empty list case
                    "video_id": video_id,
                    "sentiment_flag": 0,
                    "emotional_genre": "Error",
                    "sega_genre": "Error"
                }
        
        return data

    except Exception as e:
        print(f"Error analyzing {video_id}: {e}")
        return {
            "video_id": video_id,
            "sentiment_flag": 0,
            "emotional_genre": "Error",
            "sega_genre": "Error"
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