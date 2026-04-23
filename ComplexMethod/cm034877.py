def _extract_text(result: dict[str, Any]) -> str:
    """Extract text from OCR result."""
    if not isinstance(result, dict):
        raise ValueError("Invalid API response: top-level response must be an object")

    raw_result = result.get("result")
    if not isinstance(raw_result, dict):
        raise ValueError("Invalid API response: missing 'result' object")

    pages = raw_result.get("ocrResults")
    if not isinstance(pages, list):
        raise ValueError("Invalid API response: result.ocrResults must be an array")

    all_text = []
    for i, item in enumerate(pages):
        if not isinstance(item, dict):
            raise ValueError(
                f"Invalid API response: result.ocrResults[{i}] must be an object"
            )

        pruned = item.get("prunedResult")
        if not isinstance(pruned, dict):
            raise ValueError(
                f"Invalid API response: result.ocrResults[{i}].prunedResult must be an object"
            )

        texts = pruned.get("rec_texts", [])
        if not isinstance(texts, list):
            raise ValueError(
                f"Invalid API response: result.ocrResults[{i}].prunedResult.rec_texts "
                "must be an array"
            )
        line_parts: list[str] = []
        for j, t in enumerate(texts):
            if not isinstance(t, str):
                raise ValueError(
                    f"Invalid API response: result.ocrResults[{i}].prunedResult."
                    f"rec_texts[{j}] must be a string"
                )
            line_parts.append(t)
        if line_parts:
            all_text.append("\n".join(line_parts))
    return "\n\n".join(all_text)