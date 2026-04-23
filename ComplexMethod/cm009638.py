def convert_to_openai_tool(
    tool: Mapping[str, Any] | type[BaseModel] | Callable | BaseTool,
    *,
    strict: bool | None = None,
) -> dict[str, Any]:
    """Convert a tool-like object to an OpenAI tool schema.

    [OpenAI tool schema reference](https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools)

    Args:
        tool: Either a dictionary, a `pydantic.BaseModel` class, Python function, or
            `BaseTool`.

            If a dictionary is passed in, it is assumed to already be a valid OpenAI
            function, a JSON schema with top-level `title` key specified, an Anthropic
            format tool, or an Amazon Bedrock Converse format tool.
        strict: If `True`, model output is guaranteed to exactly match the JSON Schema
            provided in the function definition.

            If `None`, `strict` argument will not be included in tool definition.

    Returns:
        A dict version of the passed in tool which is compatible with the OpenAI
            tool-calling API.

    !!! warning "Behavior changed in `langchain-core` 0.3.16"

        `description` and `parameters` keys are now optional. Only `name` is
        required and guaranteed to be part of the output.

    !!! warning "Behavior changed in `langchain-core` 0.3.44"

        Return OpenAI Responses API-style tools unchanged. This includes
        any dict with `"type"` in `"file_search"`, `"function"`,
        `"computer_use_preview"`, `"web_search_preview"`.

    !!! warning "Behavior changed in `langchain-core` 0.3.63"

        Added support for OpenAI's image generation built-in tool.
    """
    # Import locally to prevent circular import
    from langchain_core.tools import Tool  # noqa: PLC0415

    if isinstance(tool, dict):
        if tool.get("type") in _WellKnownOpenAITools:
            return tool
        # As of 03.12.25 can be "web_search_preview" or "web_search_preview_2025_03_11"
        if (tool.get("type") or "").startswith("web_search_preview"):
            return tool
    if isinstance(tool, Tool) and (tool.metadata or {}).get("type") == "custom_tool":
        oai_tool = {
            "type": "custom",
            "name": tool.name,
            "description": tool.description,
        }
        if tool.metadata is not None and "format" in tool.metadata:
            oai_tool["format"] = tool.metadata["format"]
        return oai_tool
    oai_function = convert_to_openai_function(tool, strict=strict)
    return {"type": "function", "function": oai_function}