def _parse_tool_arguments(self, args_str: str) -> dict[str, Any]:
        """Parse tool arguments from a string like 'arg1="value1", arg2=123'.

        Supports:
        - String values: arg="value"
        - Numbers: arg=123 or arg=1.5
        - Variable references: arg=#E1
        - JSON arrays: arg=[{...}]
        - JSON objects: arg={...}
        - Booleans: arg=true/false
        """
        arguments: dict[str, Any] = {}

        # Try to parse as JSON-like structure
        # Handle both JSON format ("key": value) and Python format (key=value)
        try:
            json_str = args_str.strip()

            # Convert Python-style key=value to JSON-style "key": value
            # Match: word= at start or after comma, followed by any value
            json_str = re.sub(r"(?:^|,\s*)(\w+)\s*=\s*", r'"\1": ', json_str)

            # Wrap in braces
            json_str = "{" + json_str + "}"

            # Fix common Python-isms: single quotes -> double, True/False -> true/false
            json_str = json_str.replace("'", '"')
            json_str = re.sub(r"\bTrue\b", "true", json_str)
            json_str = re.sub(r"\bFalse\b", "false", json_str)
            json_str = re.sub(r"\bNone\b", "null", json_str)

            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

        # Fall back to regex-based parsing for simpler cases
        # Pattern for key=value where value can be:
        # - quoted string: "..."
        # - variable reference: #E1
        # - number: 123 or 1.5
        # - boolean: true/false
        arg_pattern = re.compile(
            r'(\w+)\s*=\s*(?:"([^"]*)"|(#E\d+)|(\d+\.?\d*)|(true|false))',
            re.IGNORECASE,
        )

        for match in arg_pattern.finditer(args_str):
            key = match.group(1)
            if match.group(2) is not None:  # String value
                arguments[key] = match.group(2)
            elif match.group(3) is not None:  # Variable reference
                arguments[key] = match.group(3)
            elif match.group(4) is not None:  # Number
                num_str = match.group(4)
                arguments[key] = float(num_str) if "." in num_str else int(num_str)
            elif match.group(5) is not None:  # Boolean
                arguments[key] = match.group(5).lower() == "true"

        return arguments