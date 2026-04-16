from __future__ import annotations

import os

from .providers import FallbackProvider, LLMProvider, MockProvider, NoopProvider, OllamaProvider


def get_llm_provider() -> tuple[LLMProvider, dict[str, object]]:
    """
    Returns (provider, status_dict) where status_dict is safe to expose via API.

    Defaults to Ollama with graceful fallback behavior:
    - If Ollama is down, API endpoints should continue to work in retrieval-only mode.
    """

    provider_name = (os.getenv("LLM_PROVIDER", "ollama") or "ollama").strip().lower()

    if provider_name == "mock":
        provider: LLMProvider = MockProvider()
    elif provider_name == "fallback":
        provider = FallbackProvider([OllamaProvider(), NoopProvider()])
    else:
        provider = FallbackProvider([OllamaProvider(), NoopProvider()])

    status = {
        "provider": getattr(provider, "name", "unknown"),
        "model": getattr(provider, "model", ""),
        "base_url": getattr(provider, "base_url", ""),
        "fallback_mode": isinstance(provider, FallbackProvider),
    }
    return provider, status
