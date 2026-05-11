from __future__ import annotations
import os
from typing import Optional, Tuple
from nano_schema.extractors.base import BaseExtractor


class OpenAICompatExtractor(BaseExtractor):
    """Works with OpenAI, Groq, Mistral, Ollama, nano-proxy."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: str = "openai",
    ):
        import openai
        proxy_url = os.environ.get("NANO_PROXY_URL") or base_url
        _key = api_key or os.environ.get(_KEY_ENV.get(provider, "OPENAI_API_KEY"), "")
        kwargs: dict = {"api_key": _key or "ollama"}
        if proxy_url:
            kwargs["base_url"] = proxy_url
        elif provider == "groq":
            kwargs["base_url"] = "https://api.groq.com/openai/v1"
        elif provider == "mistral":
            kwargs["base_url"] = "https://api.mistral.ai/v1"
        elif provider == "ollama":
            kwargs["base_url"] = os.environ.get("OLLAMA_HOST", "http://localhost:11434") + "/v1"
        self._client = openai.OpenAI(**kwargs)
        self._model = model or os.environ.get("NANO_SCHEMA_MODEL", _DEFAULT_MODEL.get(provider, "gpt-4o-mini"))

    def complete(self, prompt: str, model: Optional[str] = None) -> Tuple[str, int, int]:
        m = model or self._model
        response = self._client.chat.completions.create(
            model=m,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or ""
        usage = response.usage
        in_tok = usage.prompt_tokens if usage else 0
        out_tok = usage.completion_tokens if usage else 0
        return text, in_tok, out_tok


_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}

_DEFAULT_MODEL = {
    "openai": "gpt-4o-mini",
    "groq": "llama3-8b-8192",
    "mistral": "mistral-small-latest",
    "ollama": "llama3.2",
}
