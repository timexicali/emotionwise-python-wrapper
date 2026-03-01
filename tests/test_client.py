import httpx
import pytest

from emotionwise import EmotionwiseAPIError, EmotionwiseAuthError, EmotionwiseClient


def test_rejects_missing_api_key() -> None:
    with pytest.raises(EmotionwiseAuthError):
        EmotionwiseClient()


def test_api_key_header_is_sent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "test-key"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        resp = client.analyze(text="hello")
        assert resp["ok"] is True


def test_feedback_uses_api_key_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "test-key"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        resp = client.submit_feedback(prediction_id="123", vote="up")
        assert resp["ok"] is True


def test_raises_api_error_on_4xx() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Unauthorized"})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="bad", client=http_client)
        with pytest.raises(EmotionwiseAPIError) as exc:
            client.analyze(text="hello")
        assert exc.value.status_code == 401
