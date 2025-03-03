from pydantic import BaseModel

# Pydantic models for requests
class ChatRequest(BaseModel):
    prompt: str

class UploadRequest(BaseModel):
    image: str

class ImageAnalysisRequest(BaseModel):
    image: str
    prompt: str = "Describe the image."

