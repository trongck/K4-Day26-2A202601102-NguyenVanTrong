"""Small helpers shared by the demonstration clients."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def server_parameters(script_name: str):
    from mcp import StdioServerParameters

    return StdioServerParameters(
        command=sys.executable,
        args=[str(BASE_DIR / script_name)],
        env=dict(os.environ),
    )


def tool_payload(result: Any) -> dict[str, Any]:
    """Extract a dictionary from MCP structured or text tool output."""
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        if set(structured) == {"result"} and isinstance(structured["result"], dict):
            return structured["result"]
        return structured
    for item in getattr(result, "content", []):
        text = getattr(item, "text", None)
        if text:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
    raise RuntimeError("Tool không trả về JSON object hợp lệ")


def resource_payload(result: Any) -> dict[str, Any]:
    for item in result.contents:
        text = getattr(item, "text", None)
        if text:
            return json.loads(text)
    raise RuntimeError("Resource server://info không chứa JSON text")


def exception_summary(exc: BaseException) -> str:
    """Return the deepest useful exception message without a long ExceptionGroup."""
    nested = getattr(exc, "exceptions", None)
    if nested:
        return exception_summary(nested[0])
    return f"{type(exc).__name__}: {exc}"
