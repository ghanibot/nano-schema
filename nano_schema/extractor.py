from __future__ import annotations
import json
import time
from typing import Any, Optional, Type, TypeVar

from nano_schema.schema_builder import build_prompt, parse_response, build_json_schema
from nano_schema.types import ExtractionResult, ExtractionError

T = TypeVar("T")

_DEFAULT_MAX_RETRIES = 3


class SchemaExtractor:
    """
    Main extraction engine.

    Door 1 — standalone:
        extractor = SchemaExtractor(provider="anthropic")
        result = extractor.extract(MySchema, text)

    Door 2 — nano-eco (NANO_PROXY_URL env var routes through nano-proxy):
        os.environ["NANO_PROXY_URL"] = "http://localhost:8768"
        extractor = SchemaExtractor()  # auto-routes
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ):
        from nano_schema.extractors.factory import get_extractor
        self._extractor = get_extractor(provider=provider, model=model, api_key=api_key, base_url=base_url)
        self._model = model
        self._max_retries = max_retries

    def extract(
        self,
        cls: Type[T],
        text: str,
        instructions: str = "",
        model: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Extract structured data from text into cls (dataclass).
        Retries up to max_retries on parse failure.
        Returns ExtractionResult — never raises.
        """
        prompt = build_prompt(cls, text, instructions)
        last_error: Optional[str] = None
        raw = ""
        in_tok = out_tok = 0

        for attempt in range(1, self._max_retries + 1):
            try:
                raw, in_tok, out_tok = self._extractor.complete(prompt, model=model or self._model)
                data = parse_response(raw, cls)
                return ExtractionResult(
                    success=True,
                    data=data,
                    raw=raw,
                    attempts=attempt,
                    schema_name=cls.__name__,
                    model=model or self._model or "",
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                )
            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"
                if attempt < self._max_retries:
                    prompt = _repair_prompt(prompt, raw, str(e))
            except Exception as e:
                last_error = str(e)

        return ExtractionResult(
            success=False,
            data=None,
            raw=raw,
            attempts=self._max_retries,
            error=last_error,
            schema_name=cls.__name__,
            model=model or self._model or "",
            input_tokens=in_tok,
            output_tokens=out_tok,
        )

    def extract_or_raise(self, cls: Type[T], text: str, **kwargs) -> T:
        """Extract and return data directly. Raises ExtractionError on failure."""
        return self.extract(cls, text, **kwargs).unwrap()

    def schema(self, cls: type) -> dict:
        """Return JSON Schema dict for cls."""
        return build_json_schema(cls)


def _repair_prompt(original_prompt: str, bad_response: str, error: str) -> str:
    return (
        original_prompt
        + f"\n\nYour previous response was invalid JSON:\n{bad_response}\n\nError: {error}\n\n"
        "Fix the JSON and return ONLY valid JSON, nothing else:\n\nJSON:"
    )
