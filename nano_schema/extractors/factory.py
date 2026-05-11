from __future__ import annotations
import os
from typing import Optional
from nano_schema.extractors.base import BaseExtractor


def get_extractor(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> BaseExtractor:
    p = provider or os.environ.get("NANO_SCHEMA_PROVIDER", "anthropic")

    if p == "anthropic":
        from nano_schema.extractors.anthropic import AnthropicExtractor
        return AnthropicExtractor(api_key=api_key, model=model, base_url=base_url)
    elif p in ("openai", "groq", "mistral", "ollama"):
        from nano_schema.extractors.openai_compat import OpenAICompatExtractor
        return OpenAICompatExtractor(api_key=api_key, model=model, base_url=base_url, provider=p)
    else:
        raise ValueError(f"Unknown provider: {p}. Supported: anthropic, openai, groq, mistral, ollama")
