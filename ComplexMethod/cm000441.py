def get_dynamic_field_description(field_name: str) -> str:
    """
    Generate a description for a dynamic field based on its structure.

    Args:
        field_name: The full dynamic field name (e.g., "values_#_name")

    Returns:
        A descriptive string explaining what this dynamic field represents
    """
    base_name = extract_base_field_name(field_name)

    if DICT_SPLIT in field_name:
        # Extract the key part after _#_
        parts = field_name.split(DICT_SPLIT)
        if len(parts) > 1:
            key = parts[1].split("_")[0] if "_" in parts[1] else parts[1]
            return f"Dictionary field '{key}' for base field '{base_name}' ({base_name}['{key}'])"
    elif LIST_SPLIT in field_name:
        # Extract the index part after _$_
        parts = field_name.split(LIST_SPLIT)
        if len(parts) > 1:
            index = parts[1].split("_")[0] if "_" in parts[1] else parts[1]
            return (
                f"List item {index} for base field '{base_name}' ({base_name}[{index}])"
            )
    elif OBJC_SPLIT in field_name:
        # Extract the attribute part after _@_
        parts = field_name.split(OBJC_SPLIT)
        if len(parts) > 1:
            # Get the full attribute name (everything after _@_)
            attr = parts[1]
            return f"Object attribute '{attr}' for base field '{base_name}' ({base_name}.{attr})"

    return f"Value for {field_name}"