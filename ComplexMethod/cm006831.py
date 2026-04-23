async def _validate_connection_params(mode: str, command: str | None = None, url: str | None = None) -> None:
    """Validate connection parameters based on mode."""
    if mode not in ["Stdio", "Streamable_HTTP", "SSE"]:
        msg = f"Invalid mode: {mode}. Must be either 'Stdio', 'Streamable_HTTP', or 'SSE'"
        raise ValueError(msg)

    if mode == "Stdio" and not command:
        msg = "Command is required for Stdio mode"
        raise ValueError(msg)
    if mode == "Stdio" and command:
        _validate_node_installation(command)
    if mode in ["Streamable_HTTP", "SSE"] and not url:
        msg = f"URL is required for {mode} mode"
        raise ValueError(msg)