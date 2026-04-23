def validate_f_string_template(template: str) -> list[str]:
    """Validate an f-string template and return its input variables."""
    input_variables = set()
    for var, format_spec in _parse_f_string_fields(template):
        if "." in var or "[" in var or "]" in var:
            msg = (
                f"Invalid variable name {var!r} in f-string template. "
                f"Variable names cannot contain attribute "
                f"access (.) or indexing ([])."
            )
            raise ValueError(msg)

        if var.isdigit():
            msg = (
                f"Invalid variable name {var!r} in f-string template. "
                f"Variable names cannot be all digits as they are interpreted "
                f"as positional arguments."
            )
            raise ValueError(msg)

        if format_spec and ("{" in format_spec or "}" in format_spec):
            msg = (
                "Invalid format specifier in f-string template. "
                "Nested replacement fields are not allowed."
            )
            raise ValueError(msg)

        input_variables.add(var)

    return sorted(input_variables)