from __future__ import annotations
from typing import Any, Optional, Type, TypeVar

T = TypeVar("T")


def extract_guarded(
    cls: Type[T],
    text: str,
    guard=None,
    **kwargs,
) -> T:
    """
    Extract with nano-guard scan on input text before extraction.
    Raises GuardViolationError if input blocked.

    Usage:
        from nano_schema.integrations.nano_guard import extract_guarded
        result = extract_guarded(Invoice, raw_text)
    """
    if guard is None:
        try:
            from nano_guard import Guard
            guard = Guard()
        except ImportError:
            pass

    if guard is not None:
        scan_result = guard.scan(text)
        if scan_result.blocked:
            from nano_guard.guard import GuardViolationError
            raise GuardViolationError(scan_result)
        text = scan_result.redacted_text

    from nano_schema.decorators import extract
    return extract(cls, text, **kwargs)
