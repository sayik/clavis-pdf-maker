"""Render Clavis treatment-plan JSON to PDF bytes or upload to a presigned S3 URL."""
from __future__ import annotations

import base64
import json
import mimetypes
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import CSS, HTML

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

_jinja = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(("html", "xml")),
)


def _validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Lightweight shape validation; use JSON Schema/Pydantic if you need strict contracts."""
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")
    if not isinstance(payload.get("patient"), dict) or not payload["patient"].get("name"):
        raise ValueError("payload.patient.name is required")
    for key in ("doctor", "clinic", "plan"):
        if key not in payload or not isinstance(payload[key], dict):
            raise ValueError(f"payload.{key} must be an object")
    for key in ("diagnoses", "lab_results", "medications", "dietary_recommendations",
                "lifestyle_steps", "additional_tests", "notes", "references"):
        value = payload["plan"].get(key, [])
        if value is None:
            payload["plan"][key] = []
        elif not isinstance(value, list):
            raise ValueError(f"payload.plan.{key} must be a list")
    return payload


def render_pdf(payload: dict[str, Any]) -> bytes:
    """Render a JSON-compatible payload to a PDF byte string."""
    payload = _validate_payload(payload)
    template = _jinja.get_template("treatment_plan.html")
    html = template.render(
        plan=payload["plan"],
        patient=payload["patient"],
        doctor=payload["doctor"],
        clinic=payload["clinic"],
    )
    stylesheet = CSS(filename=str(STATIC_DIR / "treatment-plan.css"))
    return HTML(
        string=html,
        base_url=str(BASE_DIR),
        media_type="print",
    ).write_pdf(stylesheets=[stylesheet])


def upload_pdf_to_presigned_url(
    pdf_bytes: bytes,
    presigned_url: str,
    *,
    timeout_seconds: int = 30,
) -> None:
    """PUT a PDF to an S3 presigned URL. The URL must be generated for HTTP PUT."""
    parsed = urlparse(presigned_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("A valid HTTPS presigned URL is required")
    response = requests.put(
        presigned_url,
        data=pdf_bytes,
        headers={"Content-Type": "application/pdf"},
        timeout=timeout_seconds,
    )
    if not response.ok:
        raise RuntimeError(
            f"Presigned S3 upload failed with HTTP {response.status_code}: "
            f"{response.text[:300]}"
        )


def render_and_upload(payload: dict[str, Any], presigned_url: str) -> dict[str, Any]:
    """Convenience helper returning safe metadata; never returns/logs the presigned URL."""
    pdf_bytes = render_pdf(payload)
    upload_pdf_to_presigned_url(pdf_bytes, presigned_url)
    return {
        "status": "uploaded",
        "content_type": "application/pdf",
        "size_bytes": len(pdf_bytes),
        "filename": safe_filename(payload),
    }


def safe_filename(payload: dict[str, Any]) -> str:
    """Create a non-sensitive default filename; don't put patient names in object keys."""
    plan_id = str(payload.get("plan", {}).get("id") or "treatment-plan")
    clean = "".join(c for c in plan_id if c.isalnum() or c in ("-", "_"))[:60]
    return f"{clean or 'treatment-plan'}.pdf"


def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Render a Clavis treatment plan PDF.")
    parser.add_argument("json_file", help="Path to a treatment plan JSON file")
    parser.add_argument("--output", default="treatment-plan.pdf", help="Output PDF path")
    parser.add_argument("--presigned-url", help="Optional S3 presigned PUT URL")
    args = parser.parse_args()

    payload = load_json(args.json_file)
    pdf = render_pdf(payload)
    if args.presigned_url:
        upload_pdf_to_presigned_url(pdf, args.presigned_url)
        print(f"Uploaded {len(pdf)} bytes to the presigned URL.")
    else:
        Path(args.output).write_bytes(pdf)
        print(f"Wrote {len(pdf)} bytes to {args.output}")
