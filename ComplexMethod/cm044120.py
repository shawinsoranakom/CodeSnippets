def validate_methods(cls, v: str | list[str] | None) -> list[HTTPMethod] | None:
        """Normalize and validate HTTP methods."""
        if v is None:
            return None

        # Handle single string
        if isinstance(v, str):
            v = [v]

        if not isinstance(v, list):
            raise ValueError("methods must be a list of strings")

        # If '*' is present, it should be the only method
        if "*" in v and len(v) > 1:
            raise ValueError("Method '*' cannot be mixed with other HTTP methods.")

        # Validate each method
        validated_methods = []
        for method in v:
            method_str = str(method).upper().strip() if method != "*" else "*"
            try:
                validated_methods.append(HTTPMethod(method_str))
            except ValueError as exc:
                valid_methods = [m.value for m in HTTPMethod]
                raise ValueError(
                    f"Invalid HTTP method '{method}'. Valid methods: {', '.join(valid_methods)}"
                ) from exc

        # Remove duplicates while preserving order
        seen = set()
        unique_methods = []
        for method in validated_methods:
            if method not in seen:
                seen.add(method)
                unique_methods.append(method)

        return unique_methods if unique_methods else None