def combine(*args: Any, recursive: bool = False) -> dict[Any, Any]:
        """Combine multiple dictionaries into one."""
        if not args:
            raise TypeError("combine expected at least 1 argument, got 0")

        result: dict[Any, Any] = {}
        for arg in args:
            if not isinstance(arg, dict):
                raise TypeError(f"combine expected a dict, got {type(arg).__name__}")

            if recursive:
                for key, value in arg.items():
                    if (
                        key in result
                        and isinstance(result[key], dict)
                        and isinstance(value, dict)
                    ):
                        result[key] = FunctionalExtension.combine(
                            result[key], value, recursive=True
                        )
                    else:
                        result[key] = value
            else:
                result |= arg

        return result