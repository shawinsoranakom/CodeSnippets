def data_to_messages(data: list[Data | Message]) -> list[BaseMessage]:
    """Convert a list of data to a list of messages.

    Args:
        data (List[Data | Message]): The data to convert.

    Returns:
        List[BaseMessage]: The data as messages, filtering out any with empty content.
    """
    messages = []
    for value in data:
        try:
            lc_message = value.to_lc_message()
            # Only add messages with non-empty content (prevents Anthropic API errors)
            content = lc_message.content
            if content and ((isinstance(content, str) and content.strip()) or (isinstance(content, list) and content)):
                messages.append(lc_message)
            else:
                logger.warning("Skipping message with empty content in chat history")
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to convert message to BaseMessage: {e}")
            continue
    return messages