from __future__ import annotations

from typing import Any

import httpx

from .errors import EmotionwiseAPIError, EmotionwiseAuthError


class EmotionwiseClient:
    def __init__(
        self,
        *,
        base_url: str = "https://api.emotionwise.ai",
        api_key: str | None = None,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise EmotionwiseAuthError("api_key is required.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def _build_headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        final_headers: dict[str, str] = {}
        if headers:
            final_headers.update(headers)
        final_headers["Accept"] = "application/json"
        final_headers["X-API-Key"] = self.api_key
        return final_headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        path = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{path}"
        response = self._client.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json,
            headers=self._build_headers(headers),
        )

        if response.status_code >= 400:
            parsed_body: Any
            try:
                parsed_body = response.json()
            except ValueError:
                parsed_body = response.text
            message = f"Emotionwise API error ({response.status_code})"
            raise EmotionwiseAPIError(
                message,
                status_code=response.status_code,
                response_body=parsed_body,
            )

        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def detect_emotion(
        self,
        *,
        message: str,
        context: str | None = None,
        endpoint: str = "/api/v1/tools/emotion-detector",
        extra: dict[str, Any] | None = None,
    ) -> Any:
        if len(message) < 1 or len(message) > 1000:
            raise ValueError("message length must be between 1 and 1000 characters.")

        reserved = {"message", "context"}
        payload: dict[str, Any] = {"message": message}
        if context is not None:
            payload["context"] = context
        if extra:
            conflicts = reserved & extra.keys()
            if conflicts:
                raise ValueError(
                    f"extra must not override reserved keys: {sorted(conflicts)}"
                )
            payload.update(extra)
        return self.request("POST", endpoint, json=payload)

    def submit_feedback(
        self,
        *,
        text: str,
        predicted_emotions: list[str],
        suggested_emotions: list[str] | None = None,
        predicted_sarcasm: bool | None = None,
        sarcasm_feedback: bool | None = None,
        comment: str | None = None,
        language_code: str = "en",
        endpoint: str = "/api/v1/feedback/submit",
    ) -> Any:
        payload: dict[str, Any] = {
            "text": text,
            "predicted_emotions": predicted_emotions,
            "language_code": language_code,
        }
        if suggested_emotions is not None:
            payload["suggested_emotions"] = suggested_emotions
        if predicted_sarcasm is not None:
            payload["predicted_sarcasm"] = predicted_sarcasm
        if sarcasm_feedback is not None:
            payload["sarcasm_feedback"] = sarcasm_feedback
        if comment is not None:
            payload["comment"] = comment
        return self.request("POST", endpoint, json=payload)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "EmotionwiseClient":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()
