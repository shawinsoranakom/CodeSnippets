def recursive_eval(self, data: Any) -> Any:
        """Recursively evaluate string values in a dictionary or list.

        If the value is a string that can be evaluated, it will be evaluated.
        Otherwise, the original value is returned.
        """
        if isinstance(data, dict):
            return {k: self.recursive_eval(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self.recursive_eval(item) for item in data]
        if isinstance(data, str):
            try:
                # Only attempt to evaluate strings that look like Python literals
                if (
                    data.strip().startswith(("{", "[", "(", "'", '"'))
                    or data.strip().lower() in ("true", "false", "none")
                    or data.strip().replace(".", "").isdigit()
                ):
                    return ast.literal_eval(data)
                # return data
            except (ValueError, SyntaxError, TypeError, MemoryError):
                # If evaluation fails for any reason, return the original string
                return data
            else:
                return data
        return data