"""OllamaBase class for Ollama API clients."""
import asyncio
from typing import List, Optional

from fastapi import HTTPException
import ollama
import base64
import requests

class OllamaBase:
    def __init__(self, ollama_host:str, api_key: str):
        self.ollama_host = ollama_host
        self.api_key = api_key
        self.client = ollama.Client(
            host=self.ollama_host,
            headers={'OLLAMA_API_KEY':self.api_key}
        )

    def _check_api_key(self) -> str:
        """
        Checks if an API key is present; raise 500 if missing.
        """
        if not self.api_key:
            raise HTTPException(
                status_code=500,
                detail="No API key found. Make sure OLLAMA_API_KEY is set in .env."
            )
        return self.api_key

    def _call_ollama_chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        images: Optional[List[bytes]] = None
    ):
        """
        Wraps ollama.chat or ollama.generate calls in a single method.
        - 'model': if you want to specify a custom model like 'llama3.2'
        - 'images': for image-based queries
        """
        if self.api_key is None:
            self._check_api_key()

        try:
            response = self.client.chat(model=model or 'llama3.2',
                messages=[{
                    'role': 'user',
                    'content': prompt,
                },
            ])

            return response
        except Exception as exc:
            print(f"Error communicating with Ollama: {exc}")
            raise HTTPException(status_code=500, detail="Failed to communicate with Ollama")


    def _call_image_analysis(self, prompt: str, image_path: str, model: str = "llava:latest"):
        if self.api_key is None:
            self._check_api_key()

        # Encode image into Base64
        with open(image_path, "rb") as f:
            raw_bytes = f.read()
        encoded_str = base64.b64encode(raw_bytes).decode("utf-8")

        # Prepare the payload
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "images": [encoded_str],
            "stream": False
        }

        # Post to Ollama’s /chat or /generate endpoint
        # (the path can differ based on your version/config)
        # Typically it’s:  http://<ollama_host>:<port>/api/chat
        # or if you're connecting to the default local Docker, it might be:
        # http://127.0.0.1:11411/api/chat
        url = f"{self.ollama_host}/api/chat"
        headers = {
            "Content-Type": "application/json",
            "OLLAMA_API_KEY": self.api_key,
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error communicating with Ollama: {e}"
            )


    async def analyze_image(self, image_path: str, object_str: str, model: str = "llava:latest"):
            """
            Sends an image to Ollama for object detection and structured analysis.
            Returns: (bool is_match, str description, int confidence)
            """
            prompt_str = f"""Please analyze the image and answer the following questions:
            1. Is there a {object_str} in the image?
            2. If yes, describe its appearance and location in the image in detail.
            3. If no, describe what you see in the image instead.
            4. On a scale of 1-10, how confident are you in your answer?

            Please structure your response as follows:
            Answer: [YES/NO]
            Description: [Your detailed description]
            Confidence: [1-10]"""

            try:
                response = await asyncio.to_thread(
                    self._call_image_analysis, prompt_str, image_path, model
                )

                response_text = response.get("message", {}).get("content", "")
                response_lines = response_text.strip().split('\n')

                answer = None
                description = None
                confidence = 10  # Default confidence level

                for line in response_lines:
                    line = line.strip()
                    if line.lower().startswith('answer:'):
                        answer = line.split(':', 1)[1].strip().upper()
                    elif any(line.lower().startswith(prefix) for prefix in ['description:', 'reasoning:', 'alternative description:']):
                        description = line.split(':', 1)[1].strip()
                    elif line.lower().startswith('confidence:'):
                        try:
                            confidence = int(line.split(':', 1)[1].strip())
                        except ValueError:
                            confidence = 10  # Default confidence if parsing fails

                return answer == "YES" and confidence >= 7, description, confidence
            except Exception as e:
                print(f"Error during image analysis: {str(e)}")
                return False, "Error occurred", 0