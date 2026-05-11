from __future__ import annotations
import dataclasses
import inspect
import json
import types
import typing
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin


def build_json_schema(cls: type) -> Dict[str, Any]:
    """Convert a dataclass or annotated class to JSON Schema dict."""
    if not dataclasses.is_dataclass(cls):
        raise ValueError(f"{cls.__name__} must be a dataclass")

    props: Dict[str, Any] = {}
    required: List[str] = []

    hints = typing.get_type_hints(cls, include_extras=True)
    defaults = {f.name: f.default for f in dataclasses.fields(cls) if f.default is not dataclasses.MISSING}

    for fname, ftype in hints.items():
        if fname.startswith("_"):
            continue
        prop = _type_to_schema(ftype)

        # Pull docstring descriptions from __dataclass_fields__ metadata
        dc_field = cls.__dataclass_fields__.get(fname)
        if dc_field and dc_field.metadata.get("description"):
            prop["description"] = dc_field.metadata["description"]

        props[fname] = prop
        if fname not in defaults:
            required.append(fname)

    schema = {
        "type": "object",
        "title": cls.__name__,
        "properties": props,
    }
    if cls.__doc__ and cls.__doc__.strip():
        schema["description"] = cls.__doc__.strip()
    if required:
        schema["required"] = required

    return schema


def _type_to_schema(tp: Any) -> Dict[str, Any]:
    origin = get_origin(tp)
    args = get_args(tp)

    # Optional[X] → X, not required
    if origin is Union and len(args) == 2 and type(None) in args:
        inner = next(a for a in args if a is not type(None))
        s = _type_to_schema(inner)
        return s

    # Union[X, Y, ...]
    if origin is Union:
        return {"oneOf": [_type_to_schema(a) for a in args]}

    # List[X]
    if origin is list or origin is List:
        item_schema = _type_to_schema(args[0]) if args else {}
        return {"type": "array", "items": item_schema}

    # Dict[K, V]
    if origin is dict:
        val_schema = _type_to_schema(args[1]) if len(args) > 1 else {}
        return {"type": "object", "additionalProperties": val_schema}

    # Nested dataclass
    if dataclasses.is_dataclass(tp):
        return build_json_schema(tp)

    # Primitives
    _MAP = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        Any: {},
    }
    if tp in _MAP:
        return _MAP[tp].copy()

    # Enum
    try:
        if issubclass(tp, __builtins__["__import__"]("enum").Enum if isinstance(__builtins__, dict) else __import__("enum").Enum):
            return {"type": "string", "enum": [e.value for e in tp]}
    except (TypeError, AttributeError):
        pass

    return {"type": "string"}


def build_prompt(cls: type, source_text: str, extra_instructions: str = "") -> str:
    schema = build_json_schema(cls)
    schema_str = json.dumps(schema, indent=2)
    instructions = extra_instructions.strip()
    return f"""Extract structured information from the text below and return it as valid JSON matching this schema exactly.

Schema:
{schema_str}

Rules:
- Return ONLY valid JSON. No markdown, no explanation, no code blocks.
- Every required field must be present.
- Use null for optional fields when data is not available.
- Numbers must be numeric (not strings).
- Arrays must be arrays even if only one item.
{f"- {instructions}" if instructions else ""}

Text to extract from:
{source_text}

JSON:"""


def parse_response(response_text: str, cls: type) -> Any:
    """Parse LLM response text into dataclass instance."""
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    data = json.loads(text)
    return _dict_to_dataclass(data, cls)


def _dict_to_dataclass(data: dict, cls: type) -> Any:
    if not dataclasses.is_dataclass(cls):
        return data

    hints = typing.get_type_hints(cls)
    kwargs: Dict[str, Any] = {}

    for f in dataclasses.fields(cls):
        val = data.get(f.name)
        if val is None and f.default is not dataclasses.MISSING:
            val = f.default
        kwargs[f.name] = _coerce(val, hints.get(f.name, Any))

    return cls(**kwargs)


def _coerce(val: Any, tp: Any) -> Any:
    if val is None:
        return val

    origin = get_origin(tp)
    args = get_args(tp)

    if origin is Union and len(args) == 2 and type(None) in args:
        inner = next(a for a in args if a is not type(None))
        return _coerce(val, inner)

    if origin is list and args and isinstance(val, list):
        return [_coerce(item, args[0]) for item in val]

    if dataclasses.is_dataclass(tp) and isinstance(val, dict):
        return _dict_to_dataclass(val, tp)

    if tp is float and isinstance(val, (int, str)):
        try:
            return float(val)
        except (ValueError, TypeError):
            return val

    if tp is int and isinstance(val, (float, str)):
        try:
            return int(val)
        except (ValueError, TypeError):
            return val

    if tp is bool and isinstance(val, str):
        return val.lower() in ("true", "1", "yes")

    return val
