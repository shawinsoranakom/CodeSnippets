def get_json_schema_from_tools(
    tool_choice: str | ToolChoiceFunction | ChatCompletionNamedToolChoiceParam,
    tools: list[Tool] | None,
) -> str | dict | None:
    # tool_choice: "none"
    if tool_choice in ("none", None) or tools is None:
        return None
    # tool_choice: Forced Function (Responses)
    if (not isinstance(tool_choice, str)) and isinstance(
        tool_choice, ToolChoiceFunction
    ):
        tool_name = tool_choice.name
        tool_map = {tool.name: tool for tool in tools if isinstance(tool, FunctionTool)}
        if tool_name not in tool_map:
            raise ValueError(f"Tool '{tool_name}' has not been passed in `tools`.")
        return tool_map[tool_name].parameters
    # tool_choice: Forced Function (ChatCompletion)
    if (not isinstance(tool_choice, str)) and isinstance(
        tool_choice, ChatCompletionNamedToolChoiceParam
    ):
        tool_name = tool_choice.function.name
        tool_map = {
            tool.function.name: tool
            for tool in tools
            if isinstance(tool, ChatCompletionToolsParam)
        }
        if tool_name not in tool_map:
            raise ValueError(f"Tool '{tool_name}' has not been passed in `tools`.")
        return tool_map[tool_name].function.parameters
    # tool_choice: "required"
    if tool_choice == "required":
        return _get_json_schema_from_tools(tools)
    # tool_choice: "auto"
    return None