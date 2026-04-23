def convert_tools(tools: Sequence[Tool | ToolSchema]) -> List[ToolParam]:
    result: List[ToolParam] = []

    for tool in tools:
        if isinstance(tool, Tool):
            tool_schema = tool.schema
        else:
            assert isinstance(tool, dict)
            tool_schema = tool

        # Convert parameters to match Anthropic's schema format
        tool_params: Dict[str, Any] = {}
        if "parameters" in tool_schema:
            params = tool_schema["parameters"]

            # Transfer properties
            if "properties" in params:
                tool_params["properties"] = params["properties"]

            # Transfer required fields
            if "required" in params:
                tool_params["required"] = params["required"]

            # Handle schema type
            if "type" in params:
                tool_params["type"] = params["type"]
            else:
                tool_params["type"] = "object"

        result.append(
            ToolParam(
                name=tool_schema["name"],
                input_schema=tool_params,
                description=tool_schema.get("description", ""),
            )
        )

        # Check if the tool has a valid name
        assert_valid_name(tool_schema["name"])

    return result