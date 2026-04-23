def _recursive_eval(self, data):
        if isinstance(data, dict):
            return {k: self._recursive_eval(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._recursive_eval(item) for item in data]
        if isinstance(data, str):
            try:
                if (
                    data.strip().startswith(("{", "[", "(", "'", '"'))
                    or data.strip().lower() in ("true", "false", "none")
                    or data.strip().replace(".", "").isdigit()
                ):
                    return ast.literal_eval(data)
            except (ValueError, SyntaxError, TypeError, MemoryError):
                return data
            else:
                return data
        return data