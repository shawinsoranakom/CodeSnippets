def _convert_params_with_schema(
        self,
        function_name: str,
        param_dict: dict[str, str],
    ) -> dict[str, Any]:
        """Convert raw string param values using the tool schema types."""
        param_config: dict = {}
        if self.tools:
            for tool in self.tools:
                if (
                    hasattr(tool, "function")
                    and tool.function.name == function_name
                    and hasattr(tool.function, "parameters")
                ):
                    schema = tool.function.parameters
                    if isinstance(schema, dict) and "properties" in schema:
                        param_config = schema["properties"]
                    break

        converted: dict[str, Any] = {}
        for name, value in param_dict.items():
            param_type = "string"
            if name in param_config and isinstance(param_config[name], dict):
                param_type = param_config[name].get("type", "string")
            converted[name] = self._convert_param_value(value, param_type)
        return converted