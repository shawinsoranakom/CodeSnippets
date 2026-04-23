def _validate_parameter_name(self, param_name: str) -> bool:
        """Check if parameter exists in current function's tool definition"""
        if not self.tools or not self.current_function_name:
            return True

        for tool in self.tools:
            if (
                hasattr(tool, "type")
                and tool.type == "function"
                and hasattr(tool, "function")
                and hasattr(tool.function, "name")
                and tool.function.name == self.current_function_name
            ):
                if not hasattr(tool.function, "parameters"):
                    return True
                params = tool.function.parameters
                if isinstance(params, dict):
                    properties = params.get("properties", params)
                    return param_name in properties
                break

        return True