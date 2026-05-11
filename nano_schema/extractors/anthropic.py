from __future__ import annotations
import os
from typing import Optional, Tuple
from nano_schema.extractors.base import BaseExtractor

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AnthropicExtractor(BaseExtractor):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        import anthropic
        proxy_url = os.environ.get("NANO_PROXY_URL") or base_url
        kwargs = {"api_key": api_key or os.environ.get("ANTHROPIC_API_KEY", "")}
        if proxy_url:
            kwargs["base_url"] = proxy_url
        self._client = anthropic.Anthropic(**kwargs)
        self._model = model or os.environ.get("NANO_SCHEMA_MODEL", DEFAULT_MODEL)

    def complete(self, prompt: str, model: Optional[str] = None) -> Tuple[str, int, int]:
        m = model or self._model
        response = self._client.messages.create(
            model=m,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text if response.content else ""
        in_tok = response.usage.input_tokens if response.usage else 0
        out_tok = response.usage.output_tokens if response.usage else 0
        return text, in_tok, out_tok
