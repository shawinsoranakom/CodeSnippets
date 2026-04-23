def detect_placeholder_in_args(tool_calls: list) -> tuple[bool, str | None]:
    """Detect if any tool call contains placeholder syntax in its arguments."""
    if not tool_calls:
        return False, None

    for tool_call in tool_calls:
        args = tool_call.get("args", {})
        if isinstance(args, dict):
            for key, value in args.items():
                if isinstance(value, str) and PLACEHOLDER_PATTERN.search(value):
                    tool_name = tool_call.get("name", "unknown")
                    logger.warning(f"[IBM WatsonX] Detected placeholder: {tool_name}.{key}={value}")
                    return True, value
        elif isinstance(args, str) and PLACEHOLDER_PATTERN.search(args):
            logger.warning(f"[IBM WatsonX] Detected placeholder in args: {args}")
            return True, args
    return False, None