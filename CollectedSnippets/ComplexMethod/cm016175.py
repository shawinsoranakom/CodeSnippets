def _parse_simple_yaml(yaml_str: str) -> dict:
    """Simple YAML parser for basic configs (without external dependencies).

    Supports:
    - key: value pairs
    - booleans (true/false)
    - null values
    - integers and floats
    - strings (quoted and unquoted)
    - lists in JSON format [item1, item2, ...]
    - comments (lines starting with # or after #)

    Args:
        yaml_str: YAML content as string

    Returns:
        Dictionary containing parsed YAML content
    """
    config = {}

    for line in yaml_str.split("\n"):
        # Remove comments
        line = line.split("#")[0].strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        # Parse value based on type
        if value.lower() == "true":
            config[key] = True
        elif value.lower() == "false":
            config[key] = False
        elif value.lower() in ("null", "none", ""):
            config[key] = None
        elif value.startswith("[") and value.endswith("]"):
            # Parse list - handle quoted strings properly
            pattern = r'"([^"]+)"|\'([^\']+)\'|([^,\[\]\s]+)'
            matches = re.findall(pattern, value[1:-1])  # Remove [ ]
            parsed_items = []
            for match in matches:
                # match is a tuple of (double_quoted, single_quoted, unquoted)
                item = match[0] or match[1] or match[2]
                item = item.strip()
                if item:
                    try:
                        parsed_items.append(int(item))
                    except ValueError:
                        parsed_items.append(item)
            config[key] = parsed_items
        elif value.startswith(('"', "'")):
            config[key] = value.strip("\"'")
        else:
            # Try to parse as number
            try:
                config[key] = int(value)
            except ValueError:
                try:
                    config[key] = float(value)
                except ValueError:
                    config[key] = value

    return config