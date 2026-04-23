def convert_tools(tools: Sequence[Tool | ToolSchema]) -> List[ChatCompletionsToolDefinition]:
    result: List[ChatCompletionsToolDefinition] = []
    for tool in tools:
        if isinstance(tool, Tool):
            tool_schema = tool.schema.copy()
        else:
            assert isinstance(tool, dict)
            tool_schema = tool.copy()

        if "parameters" in tool_schema:
            for value in tool_schema["parameters"]["properties"].values():
                if "title" in value.keys():
                    del value["title"]

        function_def: Dict[str, Any] = dict(name=tool_schema["name"])
        if "description" in tool_schema:
            function_def["description"] = tool_schema["description"]
        if "parameters" in tool_schema:
            function_def["parameters"] = tool_schema["parameters"]

        result.append(
            ChatCompletionsToolDefinition(
                function=FunctionDefinition(**function_def),
            ),
        )
    return result