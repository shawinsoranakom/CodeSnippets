def _parse_tool_arguments(args_str: str) -> dict[str, str]:
    """Parse tool call arguments from the Gemma4 compact format.

    Handles the ``key:<|"|>value<|"|>`` format used by Gemma4, with fallback
    to heuristic key-value extraction. Also tolerates the slightly different
    ``key: "value"`` format (space + plain quotes) that some chat templates
    produce.

    Args:
        args_str: Raw argument string from inside ``call:name{...}``.

    Returns:
        Dictionary of argument name → value.
    """
    if not args_str or not args_str.strip():
        return {}

    # Replace Gemma4 escape tokens with standard quotes.
    cleaned = args_str.replace(_ESCAPE_TOKEN, '"')

    # Try JSON parsing first (handles nested values, arrays, etc.).
    try:
        parsed = json.loads("{" + cleaned + "}")
        # Ensure all values are strings for consistency.
        return {k: str(v) if not isinstance(v, str) else v for k, v in parsed.items()}
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: extract key:"value" pairs (allow optional space after colon).
    arguments = {}
    for key, value in re.findall(r'(\w+):\s*"([^"]*)"', cleaned):
        arguments[key] = value

    if not arguments:
        # Last resort: extract key:value pairs (unquoted).
        for key, value in re.findall(r"(\w+):\s*([^,}]+)", args_str):
            arguments[key] = value.strip().strip('"').replace(_ESCAPE_TOKEN, "")

    return arguments