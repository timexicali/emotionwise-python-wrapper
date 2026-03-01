# emotionwise-python

Python wrapper for the `emotionwise.ai` API with dual authentication support:

- `X-API-Key` for external integrations.
- `Authorization: Bearer <jwt>` for web/session flows.

## Install

```bash
pip install -e .
```

## Quick Start

```python
from emotionwise import EmotionwiseClient

client = EmotionwiseClient(
    api_key="ew_live_xxx",  # or jwt_token="..."
)

result = client.analyze(
    text="I am thrilled with the new release!",
    language="en",
    include_sarcasm=True,
)

print(result)
client.close()
```

## Notes

- Default base URL: `https://api.emotionwise.ai`
- Default analyze endpoint: `/v1/analyze`
- You can call any custom endpoint using `client.request(...)`
