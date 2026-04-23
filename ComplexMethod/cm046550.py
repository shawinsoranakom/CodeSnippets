def _translate_responses_tools_to_chat(
    tools: Optional[list[dict]],
) -> Optional[list[dict]]:
    """Translate Responses-shape function tools to the Chat Completions nested shape.

    Responses uses a flat shape per tool entry::

        {"type": "function", "name": "...", "description": "...",
         "parameters": {...}, "strict": true}

    The Chat Completions / llama-server passthrough expects the nested shape::

        {"type": "function",
         "function": {"name": "...", "description": "...",
                      "parameters": {...}, "strict": true}}

    Only ``type=="function"`` entries are forwarded. Built-in Responses tools
    (``web_search``, ``file_search``, ``mcp``, ...) are dropped because
    llama-server does not implement them server-side; keeping them in the
    request would produce an opaque upstream 400.
    """
    if not tools:
        return None
    out: list[dict] = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        if tool.get("type") != "function":
            continue
        fn: dict = {}
        if "name" in tool:
            fn["name"] = tool["name"]
        if tool.get("description") is not None:
            fn["description"] = tool["description"]
        if tool.get("parameters") is not None:
            fn["parameters"] = tool["parameters"]
        if tool.get("strict") is not None:
            fn["strict"] = tool["strict"]
        out.append({"type": "function", "function": fn})
    return out or None