def convert_to_anthropic_tool(
    tool: Mapping[str, Any] | type | Callable | BaseTool,
    *,
    strict: bool | None = None,
) -> AnthropicTool:
    """Convert a tool-like object to an Anthropic tool definition.

    Args:
        tool: A tool-like object to convert. Can be an Anthropic tool dict,
            a Pydantic model, a function, or a `BaseTool`.
        strict: If `True`, enables strict schema adherence for the tool.

            !!! note

                Requires Claude Sonnet 4.5 or Opus 4.1.

    Returns:
        `AnthropicTool` for custom/user-defined tools
    """
    if (
        isinstance(tool, BaseTool)
        and hasattr(tool, "extras")
        and isinstance(tool.extras, dict)
        and "provider_tool_definition" in tool.extras
    ):
        # Pass through built-in tool definitions
        return tool.extras["provider_tool_definition"]  # type: ignore[return-value]

    if isinstance(tool, dict) and all(
        k in tool for k in ("name", "description", "input_schema")
    ):
        # Anthropic tool format
        anthropic_formatted = AnthropicTool(tool)  # type: ignore[misc]
    else:
        oai_formatted = convert_to_openai_tool(tool, strict=strict)["function"]
        anthropic_formatted = AnthropicTool(
            name=oai_formatted["name"],
            input_schema=oai_formatted["parameters"],
        )
        if "description" in oai_formatted:
            anthropic_formatted["description"] = oai_formatted["description"]
        if "strict" in oai_formatted and isinstance(strict, bool):
            anthropic_formatted["strict"] = oai_formatted["strict"]
        # Select params from tool.extras
        if (
            isinstance(tool, BaseTool)
            and hasattr(tool, "extras")
            and isinstance(tool.extras, dict)
        ):
            for key, value in tool.extras.items():
                if key in _ANTHROPIC_EXTRA_FIELDS:
                    # all are populated top-level
                    anthropic_formatted[key] = value  # type: ignore[literal-required]
    return anthropic_formatted