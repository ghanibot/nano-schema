from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple


class BaseExtractor(ABC):
    """LLM backend for nano-schema extraction."""

    @abstractmethod
    def complete(self, prompt: str, model: Optional[str] = None) -> Tuple[str, int, int]:
        """
        Call LLM with prompt.
        Returns (response_text, input_tokens, output_tokens).
        """
        ...
