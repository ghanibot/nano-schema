import dataclasses
from typing import Optional, List
from nano_schema.schema_builder import parse_response, build_json_schema
from nano_schema.types import ExtractionResult


@dataclasses.dataclass
class Invoice:
    vendor: str
    total: float
    currency: str
    line_items: List[str]
    due_date: Optional[str] = None


def test_parse():
    mock = '{"vendor": "PT Maju Jaya", "total": 5000000.0, "currency": "IDR", "line_items": ["Web Dev", "Hosting"], "due_date": "2026-06-01"}'
    result = parse_response(mock, Invoice)
    assert result.vendor == "PT Maju Jaya"
    assert result.total == 5000000.0
    assert isinstance(result.total, float)
    assert result.line_items == ["Web Dev", "Hosting"]
    print(f"PASS: parse — vendor={result.vendor}, total={result.total}")


def test_schema():
    s = build_json_schema(Invoice)
    assert s["type"] == "object"
    assert "vendor" in s["required"]
    assert "due_date" not in s["required"]
    assert s["properties"]["total"]["type"] == "number"
    assert s["properties"]["line_items"]["type"] == "array"
    print("PASS: schema build")


def test_markdown_fence_strip():
    mock = '```json\n{"vendor": "Test", "total": 100.0, "currency": "USD", "line_items": []}\n```'
    result = parse_response(mock, Invoice)
    assert result.vendor == "Test"
    print("PASS: markdown fence strip")


if __name__ == "__main__":
    test_schema()
    test_parse()
    test_markdown_fence_strip()
    print("\nAll tests passed")
