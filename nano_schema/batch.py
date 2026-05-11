from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, List, Optional, Type, TypeVar

from nano_schema.types import ExtractionResult

T = TypeVar("T")


def extract_batch(
    cls: Type[T],
    texts: List[str],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_workers: int = 4,
    max_retries: int = 3,
) -> List[ExtractionResult]:
    """
    Extract schema from multiple texts in parallel.

    results = extract_batch(Invoice, [text1, text2, text3], max_workers=4)
    for r in results:
        if r.success:
            print(r.data.total)
    """
    from nano_schema.extractor import SchemaExtractor
    extractor = SchemaExtractor(provider=provider, model=model, max_retries=max_retries)

    results: List[Optional[ExtractionResult]] = [None] * len(texts)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(extractor.extract, cls, text): i
            for i, text in enumerate(texts)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                from nano_schema.types import ExtractionResult
                results[idx] = ExtractionResult(
                    success=False, data=None, raw="", attempts=0,
                    error=str(e), schema_name=cls.__name__,
                )

    return results  # type: ignore
