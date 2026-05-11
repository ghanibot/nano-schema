from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


@dataclass
class ExtractionResult:
    success: bool
    data: Optional[Any]          # parsed object (dataclass / dict)
    raw: str                     # raw LLM response
    attempts: int                # how many retries
    error: Optional[str] = None  # last parse error if failed
    schema_name: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0

    def unwrap(self) -> Any:
        """Return data or raise if extraction failed."""
        if not self.success or self.data is None:
            raise ExtractionError(self.error or "Extraction failed", result=self)
        return self.data


class ExtractionError(Exception):
    def __init__(self, message: str, result: Optional[ExtractionResult] = None):
        super().__init__(message)
        self.result = result


@dataclass
class SchemaField:
    name: str
    type_hint: Any
    description: str = ""
    required: bool = True
    default: Any = None
    examples: List[Any] = field(default_factory=list)
