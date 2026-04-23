def _parse_single_invoke(
        self, invoke_str: str, tools: list | None
    ) -> ToolCall | None:
        """Parse a single <invoke> block."""
        # Extract function name
        name_match = re.search(r"^([^>]+)", invoke_str)
        if not name_match:
            return None

        function_name = self._extract_name(name_match.group(1))

        # Get parameter configuration
        param_config = {}
        if tools:
            for tool in tools:
                if (
                    hasattr(tool, "function")
                    and tool.function.name == function_name
                    and hasattr(tool.function, "parameters")
                ):
                    params = tool.function.parameters
                    if isinstance(params, dict) and "properties" in params:
                        param_config = params["properties"]
                    break

        # Extract parameters
        param_dict = {}
        for match in self.parameter_complete_regex.findall(invoke_str):
            param_match = re.search(r"^([^>]+)>(.*)", match, re.DOTALL)
            if param_match:
                param_name = self._extract_name(param_match.group(1))
                param_value = param_match.group(2).strip()

                # Get parameter types (supports anyOf/oneOf/allOf)
                param_type = self._get_param_types_from_config(param_name, param_config)

                # Convert value
                param_dict[param_name] = self._convert_param_value_with_types(
                    param_value, param_type
                )

        return ToolCall(
            type="function",
            function=FunctionCall(
                name=function_name,
                arguments=json.dumps(param_dict, ensure_ascii=False),
            ),
        )