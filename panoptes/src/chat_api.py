import asyncio
import base64
import cv2
import json
import ollama
import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse

from ollama_base import OllamaBase
from util import compute_file_hash
from models import ChatRequest, UploadRequest, ImageAnalysisRequest
from constants import STORAGE_DIR, LOG_FILE, SUPPORTED_FILE_TYPES, UPLOAD_DIR, FRAMES_DIR


router = APIRouter()

class ChatAPI(OllamaBase):
    """
    A class to group Chat-related endpoints.
    We attach endpoints to a shared APIRouter instance.
    """

    def __init__(self, ollama_host:str, api_key: str):
        super().__init__(ollama_host, api_key)
        api_version = 'v1'
        # Register endpoints with the router
        router.post(f"/api/{api_version}/chat")(self.chat_endpoint)
        router.post(f"/api/{api_version}/upload")(self.upload_endpoint)
        router.post(f"/api/{api_version}/image-analysis")(self.image_analysis_endpoint)
        router.post(f"/api/{api_version}/analyze")(self.analyze_video)

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

        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1]
        if not file_extension:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file does not have a valid extension."
        )

        # Load the current log
        with open(LOG_FILE, "r") as log_file:
            log_data = json.load(log_file)

        # Save the uploaded file to a temporary location
        temp_file_path = os.path.join(STORAGE_DIR, f"temp_{uuid.uuid4()}{file_extension}")

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
        stored_filename = f"{uuid.uuid4().hex}{file_extension}"
        stored_file_path = os.path.join(STORAGE_DIR, stored_filename)
        os.rename(temp_file_path, stored_file_path)

        # Log the new file upload
        new_entry = {
            "original_filename": original_filename,
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

        print(f'>> {prompt} - {stored_file_path}')
        # Call the Ollama image analysis service
        try:
            analysis_response = self._call_image_analysis(
                prompt=prompt,
                image_path=stored_file_path
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while analyzing the image: {str(e)}"
            )

        return {
            "message": analysis_response,
            "analysis": 'Done'
        }

    # async def analyze_image(self, image_path: str, object_str: str):
    #     prompt_str = f"""Please analyze the image and answer the following questions:
    #     1. Is there a {object_str} in the image?
    #     2. If yes, describe its appearance and location in the image in detail.
    #     3. If no, describe what you see in the image instead.
    #     4. On a scale of 1-10, how confident are you in your answer?

    #     Please structure your response as follows:
    #     Answer: [YES/NO]
    #     Description: [Your detailed description]
    #     Confidence: [1-10]"""

    #     try:
    #         model = 'llama3.2-vision'
    #         # model = 'llava:latest'
    #         response = await asyncio.to_thread(
    #             ollama.chat,
    #             model=model,
    #             messages=[{
    #                 'role': 'user',
    #                 'content': prompt_str,
    #                 'images': [image_path]
    #             }]
    #         )

    #         response_text = response['message']['content']
    #         response_lines = response_text.strip().split('\n')

    #         answer = None
    #         description = None
    #         confidence = 10

    #         for line in response_lines:
    #             line = line.strip()
    #             if line.lower().startswith('answer:'):
    #                 answer = line.split(':', 1)[1].strip().upper()
    #             elif any(line.lower().startswith(prefix) for prefix in
    #                     ['description:', 'reasoning:', 'alternative description:']):
    #                 description = line.split(':', 1)[1].strip()
    #             elif line.lower().startswith('confidence:'):
    #                 try:
    #                     confidence = int(line.split(':', 1)[1].strip())
    #                 except ValueError:
    #                     confidence = 10

    #         return answer == "YES" and confidence >= 7, description, confidence
    #     except Exception as e:
    #         print(f"Error during image analysis: {str(e)}")
    #         return False, "Error occurred", 0


    def preprocess_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return False

        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        cv2.imwrite(image_path, final, [cv2.IMWRITE_JPEG_QUALITY, 100])
        return True


    # @app.get("/")
    # async def home(self, request: Request):
    #     return templates.TemplateResponse("index.html", {"request": request})


    # @app.post("/analyze")
    async def analyze_video(self,
            video: UploadFile = File(...),
            object_str: str = Form(...)
    ):
        try:
            video_path = UPLOAD_DIR / video.filename
            with open(video_path, "wb") as buffer:
                shutil.copyfileobj(video.file, buffer)

            task_frames_dir = FRAMES_DIR / video.filename.split('.')[0]
            task_frames_dir.mkdir(exist_ok=True)

            async def generate_results():
                cap = cv2.VideoCapture(str(video_path))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                frame_count = 0

                try:
                    while True:
                        success, frame = cap.read()
                        if not success:
                            break

                        # Ensure frame is valid
                        if frame is not None:
                            height, width = frame.shape[:2]

                            # if height < width:  # Portrait orientation
                            #     frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

                            if width > height:
                                # Landscape mode
                                if frame[0, 0][0] > frame[-1, -1][0]:  # Rough check for upside-down
                                    frame = cv2.rotate(frame, cv2.ROTATE_180)

                            else:
                                # Portrait mode, rotate 90 degrees
                                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

                        if frame_count % fps == 0:
                            current_second = frame_count // fps
                            frame_path = os.path.join(task_frames_dir, f"frame_{current_second}.jpg")
                            cv2.imwrite(frame_path, frame)

                            if self.preprocess_image(frame_path):
                                is_match, description, confidence = await self.analyze_image(frame_path, object_str)

                                result = {
                                    "status": "success",
                                    "frame": {
                                        "second": current_second,
                                        "is_match": is_match,
                                        "description": description,
                                        "confidence": confidence,
                                        "frame_path": f"/frames/{video.filename.split('.')[0]}/frame_{current_second}.jpg"
                                    }
                                }
                                yield json.dumps(result) + "\n"
                        frame_count += 1
                finally:
                    cap.release()

            return StreamingResponse(generate_results(), media_type="application/json")

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

