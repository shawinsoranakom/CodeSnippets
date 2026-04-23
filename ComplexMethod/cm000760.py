def process_context_field(
    context: Union[bool, dict, ContextEnabled, ContextDisabled, ContextAdvanced, None]
) -> Optional[Union[bool, Dict[str, int]]]:
    """Process context field for API payload."""
    if context is None:
        return None

    # Handle backward compatibility with boolean
    if isinstance(context, bool):
        return context if context else None
    elif isinstance(context, dict) and "maxCharacters" in context:
        return {"maxCharacters": context["maxCharacters"]}
    elif isinstance(context, ContextDisabled):
        return None  # Don't send context field at all when disabled
    elif isinstance(context, ContextEnabled):
        return True
    elif isinstance(context, ContextAdvanced):
        if context.max_characters:
            return {"maxCharacters": context.max_characters}
        return True
    return None