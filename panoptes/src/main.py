import os

from fastapi import FastAPI
from dotenv import load_dotenv

from chat_api import ChatAPI, router


load_dotenv()
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

app = FastAPI()

# Create an instance of our ChatAPI, passing in the global API key
ChatAPI(ollama_host=OLLAMA_HOST, api_key=OLLAMA_API_KEY)

# Include the router (with the two registered endpoints) in our main FastAPI app
app.include_router(router)
