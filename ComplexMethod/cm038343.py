def _validate_function_name(self, func_name: str) -> bool:
        """Check if function name exists in tool definitions"""
        if not self.tools:
            return False

        for tool in self.tools:
            if (
                hasattr(tool, "type")
                and tool.type == "function"
                and hasattr(tool, "function")
                and hasattr(tool.function, "name")
                and tool.function.name == func_name
            ):
                return True

        return False