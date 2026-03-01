import httpx
import pytest
import json

from emotionwise import EmotionwiseAPIError, EmotionwiseAuthError, EmotionwiseClient


def test_rejects_missing_api_key() -> None:
    with pytest.raises(EmotionwiseAuthError):
        EmotionwiseClient()


def test_api_key_header_is_sent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "test-key"
        assert request.url.path == "/api/v1/tools/emotion-detector"
        assert json.loads(request.content.decode("utf-8")) == {
            "message": "hello",
            "context": "daily journal",
        }
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        resp = client.detect_emotion(message="hello", context="daily journal")
        assert resp["ok"] is True


def test_feedback_uses_api_key_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "test-key"
        assert request.url.path == "/api/v1/feedback/submit"
        assert json.loads(request.content.decode("utf-8")) == {
            "text": "I am happy but a bit nervous",
            "predicted_emotions": ["joy", "nervousness"],
            "suggested_emotions": ["optimism"],
            "predicted_sarcasm": False,
            "sarcasm_feedback": None,
            "comment": "Pretty accurate",
            "language_code": "en",
        }
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        resp = client.submit_feedback(
            text="I am happy but a bit nervous",
            predicted_emotions=["joy", "nervousness"],
            suggested_emotions=["optimism"],
            predicted_sarcasm=False,
            sarcasm_feedback=None,
            comment="Pretty accurate",
            language_code="en",
        )
        assert resp["ok"] is True


def test_raises_api_error_on_4xx() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Unauthorized"})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="bad", client=http_client)
        with pytest.raises(EmotionwiseAPIError) as exc:
            client.detect_emotion(message="hello")
        assert exc.value.status_code == 401


def test_rejects_message_outside_allowed_length() -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200))) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        with pytest.raises(ValueError):
            client.detect_emotion(message="")
        with pytest.raises(ValueError):
            client.detect_emotion(message="a" * 1001)
