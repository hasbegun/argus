import base64
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


from ollama_base import OllamaBase

router = APIRouter()

# Pydantic models for requests
class ChatRequest(BaseModel):
    prompt: str

class ImageAnalysisRequest(BaseModel):
    image: str
    prompt: str = "Describe the image."


class ChatAPI(OllamaBase):
    """
    A class to group Chat-related endpoints.
    We attach endpoints to a shared APIRouter instance.
    """

    def __init__(self, ollama_host:str, api_key: str):
        super().__init__(ollama_host, api_key)

        # Register endpoints with the router
        router.post("/api/chat")(self.chat_endpoint)
        router.post("/api/image-analysis")(self.image_analysis_endpoint)

    # Endpoint 1: /api/chat
    def chat_endpoint(self, request_data: ChatRequest):
        # We won't necessarily need api_key again, because we stored a global above
        # but you could verify or override it if needed.
        response = self._call_ollama_chat(prompt=request_data.prompt)
        return {"success": True, "data": response}

    # Endpoint 2: /api/image-analysis
    def image_analysis_endpoint(
        self,
        request_data: ImageAnalysisRequest,
    ):
        # Decode Base64
        try:
            image_bytes = base64.b64decode(request_data.image)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")

        # Call Ollama with the LLaVA model
        response = self._call_ollama_chat(
            prompt=request_data.prompt,
            model="llava:latest",
            images=[image_bytes],
        )

        return {"success": True, "data": response}
