def _get_param_type(self, param_name: str) -> str:
        """Get parameter type based on tool configuration, defaults to string
        Args:
            param_name: Parameter name

        Returns:
            Parameter type
        """
        if not self.tools or not self.current_function_name:
            return "string"

        for tool in self.tools:
            if not hasattr(tool, "type") or not (
                hasattr(tool, "function") and hasattr(tool.function, "name")
            ):
                continue
            if (
                tool.type == "function"
                and tool.function.name == self.current_function_name
            ):
                if not hasattr(tool.function, "parameters"):
                    return "string"
                params = tool.function.parameters
                if isinstance(params, dict) and "properties" in params:
                    properties = params["properties"]
                    if param_name in properties and isinstance(
                        properties[param_name], dict
                    ):
                        return self.repair_param_type(
                            str(properties[param_name].get("type", "string"))
                        )
                elif isinstance(params, dict) and param_name in params:
                    param_config = params[param_name]
                    if isinstance(param_config, dict):
                        return self.repair_param_type(
                            str(param_config.get("type", "string"))
                        )
                break
        return "string"