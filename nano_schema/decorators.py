from __future__ import annotations
import dataclasses
from typing import Any, Optional, Type, TypeVar

T = TypeVar("T")

# Registry of schema classes decorated with @schema
_REGISTRY: dict[str, type] = {}


def schema(cls: type) -> type:
    """
    Decorator: mark a dataclass as a nano-schema extraction target.

    @schema
    @dataclasses.dataclass
    class Invoice:
        vendor: str
        total: float
        line_items: list[str]

    Or shorthand (auto-applies @dataclass):

    @schema
    class Invoice:
        vendor: str
        total: float
    """
    if not dataclasses.is_dataclass(cls):
        cls = dataclasses.dataclass(cls)
    _REGISTRY[cls.__name__] = cls
    return cls


def extract(
    cls: Type[T],
    text: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    instructions: str = "",
    max_retries: int = 3,
) -> T:
    """
    One-shot extraction. Creates SchemaExtractor internally.

    Usage:
        result = extract(Invoice, raw_email_text)
    """
    from nano_schema.extractor import SchemaExtractor
    extractor = SchemaExtractor(provider=provider, model=model, max_retries=max_retries)
    return extractor.extract_or_raise(cls, text, instructions=instructions)


def extract_safe(
    cls: Type[T],
    text: str,
    **kwargs,
):
    """Like extract() but returns ExtractionResult instead of raising."""
    from nano_schema.extractor import SchemaExtractor
    extractor = SchemaExtractor(
        provider=kwargs.pop("provider", None),
        model=kwargs.pop("model", None),
        max_retries=kwargs.pop("max_retries", 3),
    )
    return extractor.extract(cls, text, **kwargs)
