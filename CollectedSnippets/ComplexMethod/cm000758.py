def process_text_field(
    text: Union[bool, TextEnabled, TextDisabled, TextAdvanced, None]
) -> Optional[Union[bool, Dict[str, Any]]]:
    """Process text field for API payload."""
    if text is None:
        return None

    # Handle backward compatibility with boolean
    if isinstance(text, bool):
        return text
    elif isinstance(text, TextDisabled):
        return False
    elif isinstance(text, TextEnabled):
        return True
    elif isinstance(text, TextAdvanced):
        text_dict = {}
        if text.max_characters:
            text_dict["maxCharacters"] = text.max_characters
        if text.include_html_tags:
            text_dict["includeHtmlTags"] = text.include_html_tags
        return text_dict if text_dict else True
    return None