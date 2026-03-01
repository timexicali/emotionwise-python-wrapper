import httpx
import pytest
import json

from emotionwise import EmotionwiseAPIError, EmotionwiseAuthError, EmotionwiseClient


def test_rejects_missing_api_key() -> None:
    with pytest.raises(EmotionwiseAuthError):
        EmotionwiseClient()


def test_rejects_whitespace_api_key() -> None:
    with pytest.raises(EmotionwiseAuthError):
        EmotionwiseClient(api_key="   ")


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
            comment="Pretty accurate",
            language_code="en",
        )
        assert resp["ok"] is True


def test_feedback_omits_none_optional_fields() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        assert body == {
            "text": "hello",
            "predicted_emotions": ["joy"],
            "language_code": "en",
        }
        assert "suggested_emotions" not in body
        assert "predicted_sarcasm" not in body
        assert "sarcasm_feedback" not in body
        assert "comment" not in body
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        resp = client.submit_feedback(
            text="hello",
            predicted_emotions=["joy"],
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


def test_raises_api_error_with_text_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        with pytest.raises(EmotionwiseAPIError) as exc:
            client.detect_emotion(message="hello")
        assert exc.value.status_code == 500
        assert exc.value.response_body == "Internal Server Error"


def test_rejects_message_outside_allowed_length() -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200))) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        with pytest.raises(ValueError):
            client.detect_emotion(message="")
        with pytest.raises(ValueError):
            client.detect_emotion(message="a" * 1001)


def test_extra_cannot_override_reserved_keys() -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200))) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        with pytest.raises(ValueError, match="reserved keys"):
            client.detect_emotion(message="hello", extra={"message": "override"})


def test_request_returns_none_for_empty_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        result = client.request("DELETE", "/api/v1/resource")
        assert result is None


def test_request_returns_text_for_non_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="plain text response")

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        result = client.request("GET", "/api/v1/health")
        assert result == "plain text response"


def test_context_manager_closes_owned_client() -> None:
    with EmotionwiseClient(api_key="test-key", base_url="http://localhost") as client:
        owned_client = client._client
    assert owned_client.is_closed


def test_close_does_not_close_external_client() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200))
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="test-key", client=http_client)
        client.close()
        assert not http_client.is_closed


def test_custom_headers_cannot_override_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "real-key"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http_client:
        client = EmotionwiseClient(api_key="real-key", client=http_client)
        result = client.request(
            "GET", "/test", headers={"X-API-Key": "spoofed-key"}
        )
        assert result["ok"] is True
