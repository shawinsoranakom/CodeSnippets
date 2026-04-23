def _collect_tool_calls(results):
    """Aggregate tool calls by index from a list of DeltaMessages.

    Returns a dict: index -> {"id": ..., "name": ..., "arguments": ...}
    """
    tool_calls = {}
    for r in results:
        for tc in r.tool_calls or []:
            if tc.index not in tool_calls:
                tool_calls[tc.index] = {
                    "id": None,
                    "name": "",
                    "arguments": "",
                }
            if tc.id:
                tool_calls[tc.index]["id"] = tc.id
            if tc.function:
                if tc.function.name:
                    tool_calls[tc.index]["name"] += tc.function.name
                if tc.function.arguments:
                    tool_calls[tc.index]["arguments"] += tc.function.arguments
    return tool_calls