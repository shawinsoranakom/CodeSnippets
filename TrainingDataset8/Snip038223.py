def is_emoji(text: str) -> bool:
    """Check if input string is a valid emoji."""
    return text in ALL_EMOJIS