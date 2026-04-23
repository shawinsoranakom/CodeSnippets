def extract_reasoning_and_calls(chunks: list) -> tuple[str, list[str], list[str]]:
    """
    Extract accumulated reasoning text and tool call arguments
    from streaming chunks.
    """
    reasoning: str = ""
    tool_calls: dict[int, dict[str, str]] = {}

    for chunk in chunks:
        choice = getattr(chunk.choices[0], "delta", None)
        if not choice:
            continue

        if hasattr(choice, "reasoning") and choice.reasoning:
            reasoning += choice.reasoning

        for tc in getattr(choice, "tool_calls", []) or []:
            idx = getattr(tc, "index", 0)
            tool_entry = tool_calls.setdefault(idx, {"name": "", "arguments": ""})

            if getattr(tc, "function", None):
                func = tc.function
                if getattr(func, "name", None):
                    tool_entry["name"] = func.name
                if getattr(func, "arguments", None):
                    tool_entry["arguments"] += func.arguments

    function_names: list[str] = [v["name"] for _, v in sorted(tool_calls.items())]
    arguments: list[str] = [v["arguments"] for _, v in sorted(tool_calls.items())]

    return reasoning, arguments, function_names