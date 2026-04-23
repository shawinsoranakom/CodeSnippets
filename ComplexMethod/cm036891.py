def log_response_diagnostics(
    response,
    *,
    label: str = "Response Diagnostics",
) -> dict[str, Any]:
    """Extract and log diagnostic info from a Responses API response.

    Logs reasoning, tool-call attempts, MCP items, and output types so
    that CI output (``pytest -s`` or ``--log-cli-level=INFO``) gives
    full visibility into model behaviour even on passing runs.

    Returns the extracted data so callers can make additional assertions
    if needed.
    """
    reasoning_texts = [
        text
        for item in response.output
        if getattr(item, "type", None) == "reasoning"
        for content in getattr(item, "content", [])
        if (text := getattr(content, "text", None))
    ]

    tool_call_attempts = [
        {
            "recipient": msg.get("recipient"),
            "channel": msg.get("channel"),
        }
        for msg in response.output_messages
        if (msg.get("recipient") or "").startswith("python")
    ]

    mcp_items = [
        {
            "name": getattr(item, "name", None),
            "status": getattr(item, "status", None),
        }
        for item in response.output
        if getattr(item, "type", None) == "mcp_call"
    ]

    output_types = [getattr(o, "type", None) for o in response.output]

    diagnostics = {
        "model_attempted_tool_calls": bool(tool_call_attempts),
        "tool_call_attempts": tool_call_attempts,
        "mcp_items": mcp_items,
        "reasoning": reasoning_texts,
        "output_text": response.output_text,
        "output_types": output_types,
    }

    logger.info(
        "\n====== %s ======\n%s\n==============================",
        label,
        json.dumps(diagnostics, indent=2, default=str),
    )

    return diagnostics