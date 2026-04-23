def _parse_type(type_string: str) -> type:
        """Parse the type from the string representation."""
        # Handle Optional[T] or T | None
        if "Optional" in type_string or "|" in type_string:
            # Extract the inner type, defaulting to str if parsing fails
            match = re.search(r"Optional\[(\w+)]|(\w+)\s*\|\s*None", type_string)
            if match:
                type_string = next(
                    (group for group in match.groups() if group is not None), "str"
                )

        # Handle Literal types
        if "Literal" in type_string:
            return str  # Treat all Literal types as strings for simplicity

        # Handle Annotated types by extracting the base type
        if "Annotated" in type_string:
            match = re.search(r"Annotated\[(\w+),", type_string)
            if match:
                type_string = match.group(1)

        # Map common string representations to actual types
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "date": str,
            "datetime": str,
            "time": str,
        }
        return type_map.get(type_string, str)