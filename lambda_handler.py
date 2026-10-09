"""AWS Lambda entry point.

Expected event:
{
  "payload": { ... treatment-plan JSON ... },
  "presigned_url": "https://... S3 presigned PUT URL ..."
}

Configure API Gateway/function URL authentication outside this handler if the function
is exposed over HTTP. Prefer invoking it privately from the Clavis backend.
"""
from __future__ import annotations

from typing import Any

from renderer import render_and_upload


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise ValueError("Event must be a JSON object")
    payload = event.get("payload")
    presigned_url = event.get("presigned_url")
    if not isinstance(payload, dict):
        raise ValueError("event.payload must be an object")
    if not isinstance(presigned_url, str) or not presigned_url:
        raise ValueError("event.presigned_url is required")

    result = render_and_upload(payload, presigned_url)
    return {"statusCode": 200, "body": result}
