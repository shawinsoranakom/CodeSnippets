def convert_tool_call_to_string(tool_call: dict) -> str:
    """Convert tool call to content in string format."""
    if 'function' not in tool_call:
        raise FunctionCallConversionError("Tool call must contain 'function' key.")
    if 'id' not in tool_call:
        raise FunctionCallConversionError("Tool call must contain 'id' key.")
    if 'type' not in tool_call:
        raise FunctionCallConversionError("Tool call must contain 'type' key.")
    if tool_call['type'] != 'function':
        raise FunctionCallConversionError("Tool call type must be 'function'.")

    ret = f'<function={tool_call["function"]["name"]}>\n'
    try:
        args = json.loads(tool_call['function']['arguments'])
    except json.JSONDecodeError as e:
        raise FunctionCallConversionError(
            f'Failed to parse arguments as JSON. Arguments: {tool_call["function"]["arguments"]}'
        ) from e
    for param_name, param_value in args.items():
        # Don't add extra newlines - keep parameter value as-is
        ret += f'<parameter={param_name}>'
        if isinstance(param_value, list) or isinstance(param_value, dict):
            ret += json.dumps(param_value)
        else:
            ret += f'{param_value}'
        ret += '</parameter>\n'
    ret += '</function>'
    return ret