def convert_tools(
    tools: Sequence[Tool | ToolSchema],
) -> List[OllamaTool]:
    result: List[OllamaTool] = []
    for tool in tools:
        if isinstance(tool, Tool):
            tool_schema = tool.schema
        else:
            assert isinstance(tool, dict)
            tool_schema = tool
        parameters = tool_schema["parameters"] if "parameters" in tool_schema else None
        ollama_properties: Mapping[str, OllamaTool.Function.Parameters.Property] | None = None
        if parameters is not None:
            ollama_properties = {}
            for prop_name, prop_schema in parameters["properties"].items():
                # Determine property type, checking "type" first, then "anyOf", defaulting to "string"
                prop_type = prop_schema.get("type")
                if prop_type is None and "anyOf" in prop_schema:
                    prop_type = next(
                        (opt.get("type") for opt in prop_schema["anyOf"] if opt.get("type") != "null"),
                        None,  # Default to None if no non-null type found in anyOf
                    )
                prop_type = prop_type or "string"

                ollama_properties[prop_name] = OllamaTool.Function.Parameters.Property(
                    type=prop_type,
                    description=prop_schema["description"] if "description" in prop_schema else None,
                )
        result.append(
            OllamaTool(
                function=OllamaTool.Function(
                    name=tool_schema["name"],
                    description=tool_schema["description"] if "description" in tool_schema else "",
                    parameters=OllamaTool.Function.Parameters(
                        required=parameters["required"]
                        if parameters is not None and "required" in parameters
                        else None,
                        properties=ollama_properties,
                    ),
                ),
            )
        )
    # Check if all tools have valid names.
    for tool_param in result:
        assert_valid_name(tool_param["function"]["name"])
    return result