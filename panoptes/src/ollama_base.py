"""OllamaBase class for Ollama API clients."""

from typing import List, Optional

from fastapi import HTTPException
import ollama

class OllamaBase:
    def __init__(self, ollama_host:str, api_key: str):
        self.ollama_host = ollama_host
        self.api_key = api_key

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
            client = ollama.Client(
                host=self.ollama_host,
                headers={'OLLAMA_API_KEY':self.api_key}
            )
            response = client.chat(model=model or 'llama3.2',
                messages=[{
                    'role': 'user',
                    'content': prompt,
                },
            ])

            return response
        except Exception as exc:
            print(f"Error communicating with Ollama: {exc}")
            raise HTTPException(status_code=500, detail="Failed to communicate with Ollama")

    def _call_imagea_analysis(
        self,
        prompt: str,
        model: Optional[str] = "llava:latest",
        images: Optional[List[bytes]] = None
    ):
        """
        Wraps ollama.chat in a single method for image-based queries.
        - 'model': if you want to specify a custom model like 'llama3.2'
        - 'images': raw image bytes (PNG, JPG). Will be converted to Base64 for Ollama.
        """
        if self.api_key is None:
            self._check_api_key()

        # Convert raw image bytes to Base64 strings
        encoded_images = []
        if images:
            for img_bytes in images:
                encoded_str = base64.b64encode(img_bytes).decode('utf-8')
                encoded_images.append(encoded_str)

        try:
            response = ollama.chat(
                prompt=prompt,
                model=model,
                images=encoded_images,
                base_url=self.ollama_host,
                api_key=self.api_key
            )
            return response
        except Exception as exc:
            print(f"Error communicating with Ollama: {exc}")
            raise HTTPException(
                status_code=500,
                detail="Failed to communicate with Ollama"
            )

        # try:
        #     response = ollama.chat(
        #         prompt=prompt,
        #         model=model,
        #         images=images,
        #         base_url=self.ollama_host,
        #         api_key=self.api_key
        #     )

        #     return response
        # except Exception as exc:
        #     print(f"Error communicating with Ollama: {exc}")
        #     raise HTTPException(status_code=500, detail="Failed to communicate with Ollama")