import base64
import os
from typing import List, Optional
import shutil

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from pydantic import BaseModel


from ollama_base import OllamaBase

router = APIRouter()

STORAGE_DIR = "./store"
os.makedirs(STORAGE_DIR, exist_ok=True)

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
    async def image_analysis_endpoint(self, image: UploadFile = File(...)):
        if not (image.content_type == "image/jpeg" or image.content_type == "image/png"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only JPEG and PNG files are allowed."
            )

        # Determine the storage path
        file_path = os.path.join(STORAGE_DIR, image.filename)

        try:
            # Open the destination file in binary write mode
            with open(file_path, "wb") as f:
                # Read and write the file in chunks
                while chunk := await image.read(1024 * 1024):  # 1 MB chunks
                    f.write(chunk)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while saving the file: {str(e)}"
            )
        return {"message": "File uploaded successfully", "filename": image.filename}

        # # Read the image file from the request
        # try:
        #     image_data = await image.read()
        # except Exception:
        #     raise HTTPException(status_code=400, detail="Could not read uploaded file.")

        # if not image_data:
        #     raise HTTPException(status_code=400, detail="Empty file uploaded.")

        # # Convert the image data to a base64 string
        # b64_image = base64.b64encode(image_data).decode("utf-8")

        # # Prepare the prompt for LLaVA
        # # LLaVA typically expects a prompt format like "describe the image:\n[image]{base64_string}"
        # prompt_text = f"describe the image:\n[image]{b64_image}"

        # # Prepare the request payload for Ollama
        # payload = {
        #     "model": "llava:latest",
        #     "prompt": prompt_text
        # }

        # # Send the request to your locally running Ollama instance
        # # try:
        # #     response = requests.post("http://localhost:11411/generate", json=payload)
        # #     response.raise_for_status()
        # # except requests.exceptions.RequestException as exc:
        # #     raise HTTPException(status_code=500, detail=f"Failed to process image with Ollama: {exc}")

        # # # Return the Ollama response directly as JSON
        # # return JSONResponse(content=response.json())

        # response = self._call_imagea_analysis(
        #     prompt=payload.prompt,
        #     model=payload.model,
        #     images=[b64_image],
        # )

        # return {"success": True, "data": response}



    # def image_analysis_endpoint(
    #     self,
    #     request_data: ImageAnalysisRequest,
    # ):
    #     # 1. Decode Base64 from the incoming JSON
    #     try:
    #         image_bytes = base64.b64decode(request_data.image)
    #     except Exception:
    #         raise HTTPException(status_code=400, detail="Invalid base64 image data")

    #     # 2. Use _call_imagea_analysis to re-encode the raw bytes for Ollama
    #     response = self._call_imagea_analysis(
    #         prompt=request_data.prompt,
    #         model="llava:latest",
    #         images=[image_bytes],
    #     )

    #     return {"success": True, "data": response}


    # def image_analysis_endpoint(
    #     self,
    #     request_data: ImageAnalysisRequest,
    # ):
    #     # Decode Base64
    #     try:
    #         image_bytes = base64.b64decode(request_data.image)
    #     except Exception:
    #         raise HTTPException(status_code=400, detail="Invalid base64 image data")

    #     # Call Ollama with the LLaVA model
    #     response = self._call_ollama_chat(
    #         prompt=request_data.prompt,
    #         model="llava:latest",
    #         images=[image_bytes],
    #     )

    #     return {"success": True, "data": response}

    # async def image_analysis_endpoint(
    #     self,
    #     prompt: str = Form(...),
    #     file: UploadFile = File(...)
    # ):
    #     """
    #     Endpoint that accepts a prompt (as form-data) and a file upload.
    #     Reads the raw file bytes, calls the LLaVA model, returns the result.
    #     """
    #     try:
    #         image_bytes = await file.read()
    #     except Exception:
    #         raise HTTPException(
    #             status_code=400,
    #             detail="Failed to read uploaded file."
    #         )

    #     response = self._call_imagea_analysis(
    #         prompt=prompt,
    #         model="llava:latest",
    #         images=[image_bytes],
    #     )

    #     return {"success": True, "data": response}
