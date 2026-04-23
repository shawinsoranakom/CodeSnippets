def coerce_args(cls, values: dict) -> dict:
        """Coerce the model arguments to the correct types.

        Args:
            values: The model arguments.

        """
        content = values["content"]
        if isinstance(content, tuple):
            content = list(content)

        if not isinstance(content, (str, list)):
            try:
                values["content"] = str(content)
            except ValueError as e:
                msg = (
                    "ToolMessage content should be a string or a list of string/dicts. "
                    f"Received:\n\n{content=}\n\n which could not be coerced into a "
                    "string."
                )
                raise ValueError(msg) from e
        elif isinstance(content, list):
            values["content"] = []
            for i, x in enumerate(content):
                if not isinstance(x, (str, dict)):
                    try:
                        values["content"].append(str(x))
                    except ValueError as e:
                        msg = (
                            "ToolMessage content should be a string or a list of "
                            "string/dicts. Received a list but "
                            f"element ToolMessage.content[{i}] is not a dict and could "
                            f"not be coerced to a string.:\n\n{x}"
                        )
                        raise ValueError(msg) from e
                else:
                    values["content"].append(x)

        tool_call_id = values["tool_call_id"]
        if isinstance(tool_call_id, (UUID, int, float)):
            values["tool_call_id"] = str(tool_call_id)
        return values