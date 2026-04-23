def _extract_output_url(result: Any, context: str) -> str:
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        url = cast(Any, result.get("url"))
        if isinstance(url, str) and url:
            return url

    if isinstance(result, list) and len(result) > 0:
        first: Any = result[0]
        if isinstance(first, str) and first:
            return first
        if isinstance(first, Mapping):
            url = cast(Any, first.get("url"))
            if isinstance(url, str) and url:
                return url

    raise ValueError(f"Unexpected response from {context}: {result}")