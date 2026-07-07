"""NVIDIA LLM access through the OpenAI-compatible endpoint.

Chat:  nvidia/nemotron-3-ultra-550b-a55b (thinking togglable per call)
Embed: nvidia/nv-embedqa-e5-v5 (1024 dims, input_type passage|query)

Keys come from the environment only. Never hardcode keys here.
"""

import json
import logging

from openai import OpenAI

from .config import settings

log = logging.getLogger(__name__)


class LLMDisabled(Exception):
    """Raised when no key is configured or LLM_ENABLED is false."""


_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if not settings.llm_enabled:
        raise LLMDisabled("LLM_ENABLED is false")
    if not settings.nvidia_api_key:
        raise LLMDisabled("NVIDIA_API_KEY is not set")
    if _client is None:
        _client = OpenAI(base_url=settings.nvidia_base_url, api_key=settings.nvidia_api_key)
    return _client


def chat(messages: list[dict], think: bool = False, temperature: float = 0.2, max_tokens: int = 2048) -> str:
    """Single non-streaming chat completion. Returns the final text content."""
    extra: dict = {"chat_template_kwargs": {"enable_thinking": think}}
    if think:
        extra["reasoning_budget"] = 8192
    resp = client().chat.completions.create(
        model=settings.chat_model,
        messages=messages,
        temperature=temperature,
        top_p=0.95,
        max_tokens=max_tokens,
        extra_body=extra,
    )
    return resp.choices[0].message.content or ""


def extract_json(text: str) -> dict:
    """Pull the first JSON object out of model output, tolerant of prose around it."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object in model output: {text[:200]!r}")
    return json.loads(text[start : end + 1])


def chat_json(system: str, user: str, think: bool = False, temperature: float = 0.2, max_tokens: int = 2048) -> dict:
    """Chat call that must return a JSON object. Retries once, then raises."""
    last_exc: Exception | None = None
    for attempt in (1, 2):
        text = chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            think=think,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            return extract_json(text)
        except (ValueError, json.JSONDecodeError) as exc:
            last_exc = exc  # truncated or malformed json, one fresh sample usually fixes it
    raise last_exc


def embed(texts: list[str], input_type: str = "passage") -> list[list[float]]:
    """Embed texts. input_type is passage for stored docs, query for searches."""
    resp = client().embeddings.create(
        model=settings.embed_model,
        input=texts,
        extra_body={"input_type": input_type, "truncate": "END"},
    )
    return [d.embedding for d in resp.data]
