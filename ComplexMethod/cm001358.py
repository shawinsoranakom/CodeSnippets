def load_env_file(path: Path) -> dict[str, str]:
    """Load environment variables from a .env file.

    Handles:
    - KEY=VALUE format
    - Quoted values (single and double quotes)
    - Comments (lines starting with #)
    - Empty lines

    Args:
        path: Path to the .env file

    Returns:
        Dict mapping variable names to values
    """
    settings: dict[str, str] = {}

    if not path.exists():
        return settings

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
            if not match:
                continue

            key = match.group(1)
            value = match.group(2).strip()

            # Handle quoted values
            if len(value) >= 2:
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

            settings[key] = value

    return settings