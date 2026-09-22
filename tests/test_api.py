from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_movies():
    response = client.get("/movies")
    assert response.status_code == 200
    movies = response.json()
    assert len(movies) > 0
    assert "embedding" not in movies[0]


def test_chat_round_trip(monkeypatch):
    fake_response = MagicMock()
    fake_response.text = "I recommend The Matrix."

    fake_chat_session = MagicMock()
    fake_chat_session.send_message.return_value = fake_response

    fake_client = MagicMock()
    fake_client.chats.create.return_value = fake_chat_session

    monkeypatch.setattr("app.llm.client", fake_client)

    response = client.post("/chat", json={"message": "Recommend a sci-fi movie"})
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "I recommend The Matrix."
    assert "conversation_id" in data
