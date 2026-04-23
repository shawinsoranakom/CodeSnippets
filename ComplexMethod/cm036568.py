def _collect_from_deltas(deltas):
    """Reconstruct tool call names/args and content from a delta stream."""
    tools: dict[int, dict] = {}
    content_parts: list[str] = []
    for d in deltas:
        if d.content:
            content_parts.append(d.content)
        if d.tool_calls:
            for tc in d.tool_calls:
                func = tc.function
                if isinstance(func, dict):
                    name = func.get("name")
                    args = func.get("arguments")
                else:
                    name = getattr(func, "name", None)
                    args = getattr(func, "arguments", None)
                idx = tc.index
                if idx not in tools:
                    tools[idx] = {"name": None, "args_fragments": []}
                if name:
                    tools[idx]["name"] = name
                if args:
                    tools[idx]["args_fragments"].append(args)
    return content_parts, tools