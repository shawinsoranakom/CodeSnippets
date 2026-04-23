def sanitize_mcp_name(name: str, max_length: int = 46) -> str:
    """Sanitize a name for MCP usage by removing emojis, diacritics, and special characters.

    Args:
        name: The original name to sanitize
        max_length: Maximum length for the sanitized name

    Returns:
        A sanitized name containing only letters, numbers, hyphens, and underscores
    """
    if not name or not name.strip():
        return ""

    # Remove emojis using regex pattern
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\U00002500-\U00002bef"  # chinese char
        "\U00002702-\U000027b0"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2b55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # dingbats
        "\u3030"
        "]+",
        flags=re.UNICODE,
    )

    # Remove emojis
    name = emoji_pattern.sub("", name)

    # Normalize unicode characters to remove diacritics
    name = unicodedata.normalize("NFD", name)
    name = "".join(char for char in name if unicodedata.category(char) != "Mn")

    # Replace spaces and special characters with underscores
    name = re.sub(r"[^\w\s-]", "", name)  # Keep only word chars, spaces, and hyphens
    name = re.sub(r"[-\s]+", "_", name)  # Replace spaces and hyphens with underscores
    name = re.sub(r"_+", "_", name)  # Collapse multiple underscores

    # Remove leading/trailing underscores
    name = name.strip("_")

    # Ensure it starts with a letter or underscore (not a number)
    if name and name[0].isdigit():
        name = f"_{name}"

    # Convert to lowercase
    name = name.lower()

    # Truncate to max length
    if len(name) > max_length:
        name = name[:max_length].rstrip("_")

    # If empty after sanitization, provide a default
    if not name:
        name = "unnamed"

    return name