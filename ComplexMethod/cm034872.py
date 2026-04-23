def _extract_text(result: dict[str, Any]) -> str:
    """Extract text from document parsing result."""
    if not isinstance(result, dict):
        raise ValueError("Invalid API response: top-level response must be an object")

    raw_result = result.get("result")
    if not isinstance(raw_result, dict):
        raise ValueError("Invalid API response: missing 'result' object")

    pages = raw_result.get("layoutParsingResults")
    if not isinstance(pages, list):
        raise ValueError(
            "Invalid API response: result.layoutParsingResults must be an array"
        )

    texts = []
    for i, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ValueError(
                f"Invalid API response: result.layoutParsingResults[{i}] must be an object"
            )

        markdown = page.get("markdown")
        if not isinstance(markdown, dict):
            raise ValueError(
                f"Invalid API response: result.layoutParsingResults[{i}].markdown must be an object"
            )

        text = markdown.get("text")
        if not isinstance(text, str):
            raise ValueError(
                f"Invalid API response: result.layoutParsingResults[{i}].markdown.text must be a string"
            )
        texts.append(text)

    return "\n\n".join(texts)