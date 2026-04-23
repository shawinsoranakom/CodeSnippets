def _snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase, preserving leading/trailing underscores."""
    if not name:
        return name

    # Handle leading underscores
    leading = ""
    start_idx = 0
    while start_idx < len(name) and name[start_idx] == "_":
        leading += "_"
        start_idx += 1

    # Handle trailing underscores
    trailing = ""
    end_idx = len(name)
    while end_idx > start_idx and name[end_idx - 1] == "_":
        trailing += "_"
        end_idx -= 1

    # Convert the middle part
    middle = name[start_idx:end_idx]
    if not middle:
        return name  # All underscores

    components = middle.split("_")
    camel = components[0] + "".join(word.capitalize() for word in components[1:])

    return leading + camel + trailing