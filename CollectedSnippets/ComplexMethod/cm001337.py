def _parse_bracket_arguments(self, args_str: str) -> dict[str, Any]:
        """Parse paper-style bracket arguments: Tool[query, #E1].

        The bracket format from the paper uses simpler argument syntax:
        - Tool[search query]
        - Tool[#E1]
        - Tool[query, #E1]
        """
        args_str = args_str.strip()
        arguments: dict[str, Any] = {}

        # Empty arguments
        if not args_str:
            return arguments

        # Single variable reference
        if args_str.startswith("#E") and "," not in args_str:
            return {"input": args_str}

        # Check for key=value pairs first
        if "=" in args_str:
            # Mixed format: key=value pairs
            parts = [p.strip() for p in args_str.split(",")]
            for i, part in enumerate(parts):
                if "=" in part:
                    key, value = part.split("=", 1)
                    value = value.strip().strip("\"'")
                    arguments[key.strip()] = value
                else:
                    # Positional argument
                    arg_key = "query" if i == 0 else f"arg{i}"
                    arguments[arg_key] = part.strip().strip("\"'")
            return arguments

        # Simple format: comma-separated values
        if "," in args_str:
            parts = [p.strip() for p in args_str.split(",")]
            arguments["query"] = parts[0].strip("\"'")
            for i, part in enumerate(parts[1:], 1):
                arguments[f"arg{i}"] = part.strip().strip("\"'")
        else:
            # Single argument - treat as query
            arguments["query"] = args_str.strip("\"'")

        return arguments