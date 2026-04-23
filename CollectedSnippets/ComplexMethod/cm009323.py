def _parse_arguments_from_tool_call(
    raw_tool_call: dict[str, Any],
) -> dict[str, Any] | None:
    """Parse arguments by trying to parse any shallowly nested string-encoded JSON.

    Band-aid fix for issue in Ollama with inconsistent tool call argument structure.
    Should be removed/changed if fixed upstream.

    See https://github.com/ollama/ollama/issues/6155
    """
    if "function" not in raw_tool_call:
        return None
    function_name = raw_tool_call["function"]["name"]
    arguments = raw_tool_call["function"]["arguments"]
    parsed_arguments: dict = {}
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            # Filter out metadata fields like 'functionName' that echo function name
            if key == "functionName" and value == function_name:
                continue
            if isinstance(value, str):
                parsed_value = _parse_json_string(
                    value, skip=True, raw_tool_call=raw_tool_call
                )
                if isinstance(parsed_value, (dict, list)):
                    parsed_arguments[key] = parsed_value
                else:
                    parsed_arguments[key] = value
            else:
                parsed_arguments[key] = value
    else:
        parsed_arguments = _parse_json_string(
            arguments, skip=False, raw_tool_call=raw_tool_call
        )
    return parsed_arguments