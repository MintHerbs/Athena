
import os
from dotenv import load_dotenv
from google import genai

# 1. Load the .env file
load_dotenv()

# 2. Retrieve the key from the environment
api_key = os.getenv("GEMINI_API_KEY") # Make sure this matches your .env file exactly

if not api_key:
    raise ValueError("API Key not found. Check your .env file.")

# 3. Pass the key explicitly to the client
client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-2.0-flash", 
    contents="Explain how AI works in a few words"
)
print(response.text)
