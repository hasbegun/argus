import base64
import os
import uuid
import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse


from ollama_base import OllamaBase
from util import compute_file_hash
from validations import ChatRequest, UploadRequest, ImageAnalysisRequest
from constants import STORAGE_DIR, LOG_FILE, SUPPORTED_FILE_TYPES


router = APIRouter()

class ChatAPI(OllamaBase):
    """
    A class to group Chat-related endpoints.
    We attach endpoints to a shared APIRouter instance.
    """

    def __init__(self, ollama_host:str, api_key: str):
        super().__init__(ollama_host, api_key)

        # Register endpoints with the router
        router.post("/api/chat")(self.chat_endpoint)
        router.post("/api/upload")(self.upload_endpoint)
        router.post("/api/image-analysis")(self.image_analysis_endpoint)

    # Endpoint 1: /api/chat
    def chat_endpoint(self, request_data: ChatRequest):
        # We won't necessarily need api_key again, because we stored a global above
        # but you could verify or override it if needed.
        response = self._call_ollama_chat(prompt=request_data.prompt)
        return {"success": True, "data": response}


    # Endpoint 2: /api/upload
    async def upload_endpoint(self, file: UploadFile = File(...)):
        if file.content_type not in SUPPORTED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. JPEG, PNG, BMP, GIF, MP4, and AVI files are allowed."
            )

        # Load the current log
        with open(LOG_FILE, "r") as log_file:
            log_data = json.load(log_file)

        # Save the uploaded file to a temporary location
        temp_file_path = os.path.join(STORAGE_DIR, f"temp_{uuid.uuid4()}")

        try:
            # Open the destination file in binary write mode
            with open(temp_file_path, "wb") as f:
                # Read and write the file in chunks
                while chunk := await file.read(1024 * 1024):  # 1 MB chunks
                    f.write(chunk)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while saving the file: {str(e)}"
            )

        # Compute the hash of the uploaded file
        file_hash = compute_file_hash(temp_file_path)

        # Check for duplicates in the log
        for entry in log_data:
            if entry["hash"] == file_hash:
                # Delete the temporary file and return the existing file info
                os.remove(temp_file_path)
                return {
                    "message": "Duplicate file detected. Pointing to existing file.",
                    "filename": entry
                }

        # Generate a UUID-based filename for storage
        stored_filename = uuid.uuid4().hex
        stored_file_path = os.path.join(STORAGE_DIR, stored_filename)
        os.rename(temp_file_path, stored_file_path)

        # Log the new file upload
        new_entry = {
            "original_filename": file.filename,
            "file_type": file.content_type,
            "hash": file_hash,
            "stored_filename": stored_filename
        }

        log_data.append(new_entry)
        with open(LOG_FILE, "w") as log_file:
            json.dump(log_data, log_file, indent=4)

        return {"message": "File uploaded successfully", "filename": new_entry}

    # Endpoint 3: /api/image-analysis")
    async def image_analysis_endpoint(self,
            prompt: str = Form(...), file: UploadFile = File(...)):
        """
        Handles image upload and passes the file to the Ollama service for further analysis.
        """
        print(f"Received prompt: {prompt}")
        print(f"Received file: {file.filename}")

        # Reuse the upload routine logic
        upload_response = await self.upload_endpoint(file)
        print(f'>> {upload_response}')

        # Retrieve the stored file path
        stored_filename = upload_response.get("filename").get('stored_filename')
        stored_file_path = os.path.join(STORAGE_DIR, stored_filename)
        print(f'>> {stored_file_path}')

        # Read the stored file as bytes
        # FIXME: file io is expensive process.
        # Find a way to share the memory in upload process. It is alreay there.
        try:
            with open(stored_file_path, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing the image: {str(e)}"
            )

        # print(f'>> {base64_image}')
        # Call the Ollama image analysis service
        try:
            analysis_response = self._call_image_analysis(
                prompt=prompt,
                images=[image_bytes]
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while analyzing the image: {str(e)}"
            )

        return {
            "message": "Image analysis completed successfully.",
            "analysis": analysis_response
        }

