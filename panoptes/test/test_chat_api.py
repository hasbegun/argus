import base64
import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chat_api import ChatAPI, router

@pytest.fixture
def client():
    """
    Pytest fixture to create a test client.
    - Instantiates ChatAPI with a test API key.
    - Includes the shared router.
    - Returns a TestClient for making requests.
    """
    app = FastAPI()
    chat_api = ChatAPI(api_key="TEST_API_KEY")  # We can pass a dummy key for testing
    app.include_router(router)
    return TestClient(app)

@patch.object(ChatAPI, "_call_ollama_chat", return_value="Mocked chat response")
def test_chat_endpoint(mock_call, client):
    """
    Test the /api/chat endpoint.
    We mock _call_ollama_chat to avoid calling Ollama for real.
    """
    # Arrange
    payload = {"prompt": "Hello from test!"}

    # Act
    response = client.post("/api/chat", json=payload)
    json_data = response.json()

    # Assert
    assert response.status_code == 200
    assert json_data["success"] is True
    assert json_data["data"] == "Mocked chat response"
    # Ensure our mock was called with the expected prompt
    mock_call.assert_called_once_with("Hello from test!", model=None, images=None)

@patch.object(ChatAPI, "_call_ollama_chat", return_value="Mocked image analysis response")
def test_image_analysis_endpoint(mock_call, client):
    """
    Test the /api/image-analysis endpoint.
    """
    # Encode a dummy image (e.g. empty bytes) in base64
    dummy_image = base64.b64encode(b"FAKE_IMAGE_DATA").decode("utf-8")
    payload = {
        "image": dummy_image,
        "prompt": "Describe this test image."
    }

    response = client.post("/api/image-analysis", json=payload)
    json_data = response.json()

    assert response.status_code == 200
    assert json_data["success"] is True
    assert json_data["data"] == "Mocked image analysis response"

    # The mock should have been called with the correct arguments
    # Notice 'images' is a list with one item (the decoded bytes from our payload).
    decoded_bytes = base64.b64decode(dummy_image)
    mock_call.assert_called_once_with("Describe this test image.", model="llava:latest", images=[decoded_bytes])

def test_image_analysis_invalid_base64(client):
    """
    Test that invalid base64 data returns a 400 error.
    """
    payload = {
        "image": "NOT_BASE64_DATA!!!",
        "prompt": "Anything"
    }

    response = client.post("/api/image-analysis", json=payload)
    json_data = response.json()

    assert response.status_code == 400
    assert json_data["detail"] == "Invalid base64 image data"
