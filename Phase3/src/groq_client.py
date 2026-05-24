"""Groq LLM client via OpenAI-compatible chat completions API."""

from __future__ import annotations

import json
from typing import Any

import httpx

from src.config import (
    DEFAULT_MODEL,
    GROQ_API_KEY,
    GROQ_CHAT_COMPLETIONS_URL,
)


def is_groq_configured() -> bool:
    return bool(GROQ_API_KEY)


def chat_completions(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.2,
    json_mode: bool = True,
    timeout: float = 120.0,
) -> str:
    """
    POST https://api.groq.com/openai/v1/chat/completions
    Returns assistant message content as a string.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set")

    payload: dict[str, Any] = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            GROQ_CHAT_COMPLETIONS_URL,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices") or []
    if not choices:
        raise ValueError("Groq returned no choices")

    content = choices[0].get("message", {}).get("content")
    if not content:
        raise ValueError("Empty response from Groq")
    return content


def chat_json(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """Call Groq chat completions and parse a JSON object from the response."""
    content = chat_completions(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=temperature,
        json_mode=True,
    )
    return json.loads(content)
