def convert_tools(
    tools: Sequence[Tool | ToolSchema],
) -> List[ChatCompletionToolParam]:
    result: List[ChatCompletionToolParam] = []
    for tool in tools:
        if isinstance(tool, Tool):
            tool_schema = tool.schema
        else:
            assert isinstance(tool, dict)
            tool_schema = tool

        result.append(
            ChatCompletionToolParam(
                type="function",
                function=FunctionDefinition(
                    name=tool_schema["name"],
                    description=(tool_schema["description"] if "description" in tool_schema else ""),
                    parameters=(
                        cast(FunctionParameters, tool_schema["parameters"]) if "parameters" in tool_schema else {}
                    ),
                    strict=(tool_schema["strict"] if "strict" in tool_schema else False),
                ),
            )
        )
    # Check if all tools have valid names.
    for tool_param in result:
        assert_valid_name(tool_param["function"]["name"])
    return result