def _extract_field_type(field_info: FieldInfo) -> tuple[str, list[str]]:
    """Extract the field type and choices from a Pydantic FieldInfo.

    Returns:
        Tuple of (field_type, choices) where field_type is one of:
        "str", "int", "float", "bool", "secret", "choice"
    """
    annotation = field_info.annotation
    choices: list[str] = []

    # Unwrap Optional
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        # Filter out NoneType
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            annotation = non_none_args[0]
            origin = get_origin(annotation)

    # Check for SecretStr
    if annotation is SecretStr:
        return "secret", []

    # Check for Literal (choices)
    if origin is Literal:
        choices = list(get_args(annotation))
        return "choice", [str(c) for c in choices]

    # Check for Enum
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        choices = [e.value for e in annotation]
        return "choice", choices

    # Check basic types
    if annotation is bool:
        return "bool", []
    if annotation is int:
        return "int", []
    if annotation is float:
        return "float", []
    if annotation is str:
        return "str", []

    # Default to string
    return "str", []