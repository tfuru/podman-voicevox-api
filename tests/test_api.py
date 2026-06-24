from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("routers.synthesis.requests.post")
def test_synthesis_valid_parameters(mock_post):
    # Mock /audio_query response
    mock_query_response = MagicMock()
    mock_query_response.status_code = 200
    mock_query_response.json.return_value = {
        "accent_phrases": [],
        "speedScale": 1.0,
        "pitchScale": 0.0,
        "intonationScale": 1.0,
        "volumeScale": 1.0,
    }
    
    # Mock /synthesis response
    mock_synthesis_response = MagicMock()
    mock_synthesis_response.status_code = 200
    mock_synthesis_response.content = b"fake wav audio content"
    
    mock_post.side_effect = [mock_query_response, mock_synthesis_response]
    
    from config import settings
    headers = {"X-API-KEY": settings.ADMIN_API_KEY}
    
    payload = {
        "text": "こんにちは",
        "speaker": 2,
        "format": "wav",
        "speedScale": 1.5,
        "pitchScale": 0.1,
        "intonationScale": 1.2,
        "volumeScale": 0.8
    }
    
    response = client.post("/api/synthesis", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.content == b"fake wav audio content"
    
    # Check that mock_post was called with updated query JSON
    assert mock_post.call_count == 2
    
    # First call: audio_query
    first_call_args = mock_post.call_args_list[0]
    assert "audio_query" in first_call_args[0][0]
    
    # Second call: synthesis
    second_call_args = mock_post.call_args_list[1]
    assert "synthesis" in second_call_args[0][0]
    sent_json = second_call_args[1]["json"]
    assert sent_json["speedScale"] == 1.5
    assert sent_json["pitchScale"] == 0.1
    assert sent_json["intonationScale"] == 1.2
    assert sent_json["volumeScale"] == 0.8

def test_synthesis_invalid_parameters():
    from config import settings
    headers = {"X-API-KEY": settings.ADMIN_API_KEY}
    
    # Test speedScale out of range (too high)
    response = client.post("/api/synthesis", json={
        "text": "こんにちは",
        "speaker": 2,
        "speedScale": 2.5
    }, headers=headers)
    assert response.status_code == 422
    
    # Test pitchScale out of range (too low)
    response = client.post("/api/synthesis", json={
        "text": "こんにちは",
        "speaker": 2,
        "pitchScale": -0.2
    }, headers=headers)
    assert response.status_code == 422

    # Test intonationScale out of range (negative)
    response = client.post("/api/synthesis", json={
        "text": "こんにちは",
        "speaker": 2,
        "intonationScale": -0.5
    }, headers=headers)
    assert response.status_code == 422

    # Test volumeScale out of range (too high)
    response = client.post("/api/synthesis", json={
        "text": "こんにちは",
        "speaker": 2,
        "volumeScale": 2.1
    }, headers=headers)
    assert response.status_code == 422

