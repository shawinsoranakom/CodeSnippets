def _collect_streamed_tool_calls(chunks: list[dict]) -> list[dict]:
    """Reassemble OpenAI streaming delta.tool_calls into full tool calls.

    OpenAI streams partial tool calls across chunks — the first chunk for
    a given index carries ``id`` + ``function.name``, and subsequent
    chunks append fragments to ``function.arguments``.
    """
    by_index: dict[int, dict] = {}
    for c in chunks:
        choices = c.get("choices") or []
        if not choices:
            continue
        delta = choices[0].get("delta") or {}
        tool_calls = delta.get("tool_calls") or []
        for tc in tool_calls:
            idx = tc.get("index", 0)
            slot = by_index.setdefault(
                idx,
                {
                    "id": None,
                    "type": "function",
                    "function": {"name": None, "arguments": ""},
                },
            )
            if tc.get("id"):
                slot["id"] = tc["id"]
            fn = tc.get("function") or {}
            if fn.get("name"):
                slot["function"]["name"] = fn["name"]
            if fn.get("arguments"):
                slot["function"]["arguments"] += fn["arguments"]
    return [by_index[i] for i in sorted(by_index)]