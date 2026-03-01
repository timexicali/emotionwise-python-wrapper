# emotionwise-python

Python wrapper for the `emotionwise.ai` API using `X-API-Key` authentication.

## Install

```bash
pip install -e .
```

## Quick Start

```python
from emotionwise import EmotionwiseClient

with EmotionwiseClient(api_key="YOUR_API_KEY") as client:
    result = client.detect_emotion(
        message="I am happy but a bit nervous",
        context="daily journal",
    )
    print(result)
```

## Detector Endpoint

- `POST /api/v1/tools/emotion-detector`
- Message length: min `1`, max `1000` characters.

## Feedback Endpoint

- `POST /api/v1/feedback/submit`

Valid emotion labels:

`["admiration", "amusement", "anger", "annoyance", "approval", "caring", "confusion", "curiosity", "desire", "disappointment", "disapproval", "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief", "joy", "love", "nervousness", "optimism", "pride", "realization", "relief", "remorse", "sadness", "surprise", "neutral"]`

Example:

```python
from emotionwise import EmotionwiseClient

with EmotionwiseClient(api_key="YOUR_API_KEY") as client:
    feedback = client.submit_feedback(
        text="I am happy but a bit nervous",
        predicted_emotions=["joy", "nervousness"],
        suggested_emotions=["optimism"],
        predicted_sarcasm=False,
        comment="Pretty accurate",
        language_code="en",
    )
    print(feedback)
```

## Error Handling

- Default base URL: `https://api.emotionwise.ai`
- Common handled statuses:
  - `401`: missing or invalid API key
  - `403`: API key inactive or not allowed
  - `429`: quota or rate limit exceeded
- Non-2xx responses raise `EmotionwiseAPIError` with:
  - `status_code`
  - `response_body`

## Response Contract Notes

Detector responses include:

- `detected_emotions`
- `confidence_scores`
- `sarcasm_detected` and `sarcasm_score` (beta)
- `detected_language` and `session_id`

Policy note: do not use this API as the sole basis for legal, medical, hiring, or safety-critical decisions.
