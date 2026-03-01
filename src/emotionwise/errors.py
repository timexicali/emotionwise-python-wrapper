from __future__ import annotations

from typing import Any


class EmotionwiseError(Exception):
    """Base exception for the Emotionwise wrapper."""


class EmotionwiseAuthError(EmotionwiseError):
    """Raised when authentication setup is invalid."""


class EmotionwiseAPIError(EmotionwiseError):
    """Raised when the Emotionwise API returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        response_body: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
