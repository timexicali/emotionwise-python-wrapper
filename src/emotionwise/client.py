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
        jwt_token: str | None = None,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        if api_key and jwt_token:
            raise EmotionwiseAuthError(
                "Provide either api_key or jwt_token, not both."
            )
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def _build_headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        final_headers = {"Accept": "application/json"}
        if self.api_key:
            final_headers["X-API-Key"] = self.api_key
        if self.jwt_token:
            final_headers["Authorization"] = f"Bearer {self.jwt_token}"
        if headers:
            final_headers.update(headers)
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

    def analyze(
        self,
        *,
        text: str,
        language: str = "en",
        include_sarcasm: bool = True,
        endpoint: str = "/v1/analyze",
        extra: dict[str, Any] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "text": text,
            "language": language,
            "include_sarcasm": include_sarcasm,
        }
        if extra:
            payload.update(extra)
        return self.request("POST", endpoint, json=payload)

    def submit_feedback(
        self,
        *,
        prediction_id: str,
        vote: str,
        comment: str | None = None,
        endpoint: str = "/v1/feedback",
    ) -> Any:
        payload: dict[str, Any] = {
            "prediction_id": prediction_id,
            "vote": vote,
        }
        if comment:
            payload["comment"] = comment
        return self.request("POST", endpoint, json=payload)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "EmotionwiseClient":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()
