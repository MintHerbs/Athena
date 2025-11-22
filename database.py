import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
MONGO_URI = os.getenv("MONGO_URI") 
DATABASE_NAME = "apollo"
COLLECTION_NAME = "gemini_analysis"

# 1. Initialize client globally. This must be done here so all functions can access it.
client = None

def connect_to_db():
    """
    Establishes and tests the MongoDB connection.
    Updates the global 'client' variable.
    """
    global client
    
    if not MONGO_URI:
        print("MONGO_URI not found in environment variables. Data insertion will fail.")
        return

    try:
        # Set a server selection timeout to avoid long hangs
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Attempt to ping the server to verify the connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas!")
        
    except ConnectionFailure:
        print("Failed to connect to MongoDB Atlas: Connection timed out or URI might be incorrect.")
        client = None
    except Exception as e:
        print(f"An unexpected error occurred during connection: {e}")
        client = None

# 2. Define the insertion function (Guaranteed to be defined for import)
def insert_analysis_results(results):
    """
    Inserts a list of dictionary results into the gemini_analysis collection.
    """
    if client is None:
        print("Database client is not initialized. Cannot insert data.")
        return 0

    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    try:
        # insert_many handles the list of dictionaries
        insert_result = collection.insert_many(results)
        print(f"Successfully inserted {len(insert_result.inserted_ids)} documents.")
        return len(insert_result.inserted_ids)
        
    except OperationFailure as e:
        print(f"MongoDB Operation Error (e.g., schema validation failed): {e}")
        return 0
    except Exception as e:
        print(f"Error inserting documents: {e}")
        return 0

# 3. Call the connection function immediately when the module is loaded
# This ensures connection happens upon import, but the function definition above is safe.
connect_to_db()