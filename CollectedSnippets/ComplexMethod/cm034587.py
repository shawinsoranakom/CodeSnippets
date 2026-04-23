def format_prompt(messages: Messages, add_special_tokens: bool = False, do_continue: bool = False, include_system: bool = True) -> str:
    """
    Format a series of messages into a single string, optionally adding special tokens.

    Args:
        messages (Messages): A list of message dictionaries, each containing 'role' and 'content'.
        add_special_tokens (bool): Whether to add special formatting tokens.

    Returns:
        str: A formatted string containing all messages.
    """
    if not add_special_tokens and len(messages) <= 1:
        return to_string(messages[0]["content"])
    messages = [
        (message["role"], to_string(message["content"]))
        for message in messages
        if include_system or message.get("role") not in ("developer", "system")
    ]
    formatted = "\n".join([
        f'{role.capitalize()}: {content}'
        for role, content in messages
        if content.strip()
    ])
    if do_continue:
        return formatted
    return f"{formatted}\nAssistant:"