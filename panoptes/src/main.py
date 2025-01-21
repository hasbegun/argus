import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from ollama import Client


load_dotenv()
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

app = FastAPI()
class ChatRequest(BaseModel):
    prompt: str

@app.post("/api/chat")
def chat_endpoint(payload: ChatRequest):
    prompt = payload.prompt

    if not OLLAMA_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="No API key provided. Make sure it's set in your .env."
        )

    try:
        # Add the API key to the request headers, using "Bearer" as an example
        headers = {
            "Authorization": f"Bearer {OLLAMA_API_KEY}"
        }

        # IMPORTANT: If you're on macOS/Windows and Ollama is on the host,
        # use `host.docker.internal` instead of `localhost`.
        # If on Linux and using --network=host, you can keep "http://localhost:11411".
        # response = requests.post("http://host.docker.internal:11434/api/chat",
        #     json={"prompt": prompt},
        #     headers = headers
        # )
        client = Client(
            host=OLLAMA_HOST,
            headers={'OLLAMA_API_KEY': OLLAMA_API_KEY}
        )
        response = client.chat(model='llama3.2', messages=[
        {
            'role': 'user',
            'content': prompt,
        },
        ])
        # response = ollama.chat(api_key=OLLAMA_API_KEY, host="http://host.docker.internal:11434", prompt=prompt)
        # response.raise_for_status()
        return {
            "success": True,
            "data": response.json()
        }
    except requests.exceptions.RequestException as err:
        print(f"Error communicating with Ollama: {err}")
        raise HTTPException(status_code=500,
                            detail="Failed to communicate with Ollama")

