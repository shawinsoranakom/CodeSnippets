def parse_tool_call(
    raw_tool_call: dict[str, Any],
    *,
    partial: bool = False,
    strict: bool = False,
    return_id: bool = True,
) -> dict[str, Any] | None:
    """Parse a single tool call.

    Args:
        raw_tool_call: The raw tool call to parse.
        partial: Whether to parse partial JSON.
        strict: Whether to allow non-JSON-compliant strings.
        return_id: Whether to return the tool call id.

    Returns:
        The parsed tool call.

    Raises:
        OutputParserException: If the tool call is not valid JSON.
    """
    if "function" not in raw_tool_call:
        return None

    arguments = raw_tool_call["function"]["arguments"]

    if partial:
        try:
            function_args = parse_partial_json(arguments, strict=strict)
        except (JSONDecodeError, TypeError):  # None args raise TypeError
            return None
    # Handle None or empty string arguments for parameter-less tools
    elif not arguments:
        function_args = {}
    else:
        try:
            function_args = json.loads(arguments, strict=strict)
        except JSONDecodeError as e:
            msg = (
                f"Function {raw_tool_call['function']['name']} arguments:\n\n"
                f"{arguments}\n\nare not valid JSON. "
                f"Received JSONDecodeError {e}"
            )
            raise OutputParserException(msg) from e
    parsed = {
        "name": raw_tool_call["function"]["name"] or "",
        "args": function_args or {},
    }
    if return_id:
        parsed["id"] = raw_tool_call.get("id")
        parsed = create_tool_call(**parsed)  # type: ignore[assignment,arg-type]
    return parsed