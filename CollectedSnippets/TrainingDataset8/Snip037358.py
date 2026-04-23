def validate_emoji(maybe_emoji: Optional[str]) -> str:
    if maybe_emoji is None:
        return ""
    elif is_emoji(maybe_emoji):
        return maybe_emoji
    else:
        raise StreamlitAPIException(
            f'The value "{maybe_emoji}" is not a valid emoji. Shortcodes are not allowed, please use a single character instead.'
        )