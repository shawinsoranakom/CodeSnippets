def _remove_enum(obj: Any) -> None:
    """Remove the description from enums."""
    if isinstance(obj, dict):
        if "enum" in obj:
            if "description" in obj and obj["description"] == "An enumeration.":
                del obj["description"]
            if "type" in obj and obj["type"] == "string":
                del obj["type"]
            del obj["enum"]
        for value in obj.values():
            _remove_enum(value)
    elif isinstance(obj, list):
        for item in obj:
            _remove_enum(item)