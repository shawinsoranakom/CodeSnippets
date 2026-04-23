def _format_argument(argument: Any, escape_keys: bool = True) -> str:
            if isinstance(argument, str):
                return f'<|"|>{argument}<|"|>'

            if isinstance(argument, bool):
                return "true" if argument else "false"

            if isinstance(argument, dict):
                items: list[str] = []
                for key in sorted(argument.keys()):
                    formatted_key = f'<|"|>{key}<|"|>' if escape_keys else str(key)
                    formatted_value = _format_argument(argument[key], escape_keys=escape_keys)
                    items.append(f"{formatted_key}:{formatted_value}")
                return "{" + ",".join(items) + "}"

            if isinstance(argument, (list, tuple)):
                return "[" + ",".join(_format_argument(item, escape_keys=escape_keys) for item in argument) + "]"

            if argument is None:
                return "null"

            return str(argument)