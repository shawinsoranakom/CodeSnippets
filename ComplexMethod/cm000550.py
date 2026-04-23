def _process_tool_calls(
        self, response: Any, tool_functions: list[dict[str, Any]]
    ) -> list[ToolInfo]:
        """Process tool calls and extract tool definitions, arguments, and input data.

        Returns a list of tool info dicts with:
        - tool_call: The original tool call object
        - tool_name: The function name
        - tool_def: The tool definition from tool_functions
        - input_data: Processed input data dict (includes None values)
        - field_mapping: Field name mapping for the tool
        """
        if not response.tool_calls:
            return []

        processed_tools = []
        for tool_call in response.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            tool_def = next(
                (
                    tool
                    for tool in tool_functions
                    if tool["function"]["name"] == tool_name
                ),
                None,
            )
            if not tool_def:
                if len(tool_functions) == 1:
                    tool_def = tool_functions[0]
                else:
                    continue

            # Build input data for the tool
            input_data = {}
            field_mapping = tool_def["function"].get("_field_mapping", {})
            if "function" in tool_def and "parameters" in tool_def["function"]:
                expected_args = tool_def["function"]["parameters"].get("properties", {})
                for clean_arg_name in expected_args:
                    original_field_name = field_mapping.get(
                        clean_arg_name, clean_arg_name
                    )
                    arg_value = tool_args.get(clean_arg_name)
                    # Include all expected parameters, even if None (for backward compatibility with tests)
                    input_data[original_field_name] = arg_value

            processed_tools.append(
                ToolInfo(
                    tool_call=tool_call,
                    tool_name=tool_name,
                    tool_def=tool_def,
                    input_data=input_data,
                    field_mapping=field_mapping,
                )
            )

        return processed_tools