def load_filter_patterns(filter_file: Path) -> dict[str, list[str]]:
    """Load all patterns from the changes-filter.yaml file.

    Validates and normalizes the YAML structure to ensure it's a dict mapping
    str to list[str]. Handles top-level "filters" key if present.
    """
    with filter_file.open() as f:
        data = yaml.safe_load(f)

    # Handle empty or null file
    if data is None:
        return {}

    # If there's a top-level "filters" key, use that instead
    if isinstance(data, dict) and "filters" in data:
        data = data["filters"]

    # Ensure we have a dict
    if not isinstance(data, dict):
        msg = f"Expected dict at top level, got {type(data).__name__}"
        raise TypeError(msg)

    # Normalize and validate the structure
    result: dict[str, list[str]] = {}
    for key, value in data.items():
        # Validate key is a string
        if not isinstance(key, str):
            msg = f"Expected string key, got {type(key).__name__}: {key}"
            raise TypeError(msg)

        # Coerce single string to list
        normalized_value = [value] if isinstance(value, str) else value

        # Validate value is a list
        if not isinstance(normalized_value, list):
            msg = f"Expected list for key '{key}', got {type(normalized_value).__name__}"
            raise TypeError(msg)

        # Validate all items in the list are strings
        for i, item in enumerate(normalized_value):
            if not isinstance(item, str):
                msg = f"Expected string in list for key '{key}' at index {i}, got {type(item).__name__}"
                raise TypeError(msg)

        result[key] = normalized_value

    return result