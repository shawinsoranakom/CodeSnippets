def convert_langchain_tools_to_sparc_tool_specs_format(
        tools: list[BaseTool],
    ) -> list[dict]:
        """Convert LangChain tools to OpenAI function calling format for SPARC validation.

        SPARC expects tools in OpenAI's function calling format, which is the standard
        format used by OpenAI, Anthropic, Google, and other LLM providers for tool integration.

        Args:
            tools: List of LangChain BaseTool instances to convert

        Returns:
            List of tool specifications in OpenAI function calling format:
            [
                {
                    "type": "function",
                    "function": {
                        "name": "tool_name",
                        "description": "Tool description",
                        "parameters": {
                            "type": "object",
                            "properties": {...},
                            "required": [...]
                        }
                    }
                }
            ]
        """
        tool_specs = []

        for i, tool in enumerate(tools):
            try:
                # Handle nested wrappers
                unwrapped_tool = tool
                wrapper_count = 0

                # Unwrap to get to the actual tool
                while hasattr(unwrapped_tool, "wrapped_tool") and not isinstance(unwrapped_tool, ValidatedTool):
                    unwrapped_tool = unwrapped_tool.wrapped_tool
                    wrapper_count += 1
                    if wrapper_count > _MAX_WRAPPER_DEPTH:  # Prevent infinite loops
                        break

                # Build tool spec from LangChain tool
                tool_spec = {
                    "type": "function",
                    "function": {
                        "name": unwrapped_tool.name,
                        "description": unwrapped_tool.description or f"Tool: {unwrapped_tool.name}",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                }

                # Extract parameters from tool schema if available
                args_dict = unwrapped_tool.args
                if isinstance(args_dict, dict):
                    for param_name, param_info in args_dict.items():
                        logger.debug(f"Processing parameter: {param_name}")
                        logger.debug(f"Parameter info: {param_info}")

                        # Use the new conversion function
                        param_spec = _convert_pydantic_type_to_json_schema_type(param_info)

                        # Check if parameter is required using Pydantic model fields
                        if unwrapped_tool.args_schema and hasattr(unwrapped_tool.args_schema, "model_fields"):
                            field_info = unwrapped_tool.args_schema.model_fields.get(param_name)
                            if field_info and field_info.is_required():
                                tool_spec["function"]["parameters"]["required"].append(param_name)

                        tool_spec["function"]["parameters"]["properties"][param_name] = param_spec

                tool_specs.append(tool_spec)

            except (AttributeError, KeyError, TypeError, ValueError) as e:
                logger.warning(f"Could not convert tool {getattr(tool, 'name', 'unknown')} to spec: {e}")
                # Create minimal spec
                minimal_spec = {
                    "type": "function",
                    "function": {
                        "name": getattr(tool, "name", f"unknown_tool_{i}"),
                        "description": getattr(
                            tool,
                            "description",
                            f"Tool: {getattr(tool, 'name', 'unknown')}",
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                }
                tool_specs.append(minimal_spec)

        if not tool_specs:
            logger.error("⚠️ No tool specs were generated! This will cause SPARC validation to fail")
        return tool_specs