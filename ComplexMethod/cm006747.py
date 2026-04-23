def normalize_message_content(message: BaseMessage) -> str:
    """Normalize message content to handle inconsistent formats from Data.to_lc_message().

    Args:
        message: A BaseMessage that may have content as either:
                - str (for AI messages)
                - list[dict] (for User messages in format [{"type": "text", "text": "..."}])

    Returns:
        str: The extracted text content

    Note:
        This addresses the inconsistency in lfx.schema.data.Data.to_lc_message() where:
        - User messages: content = [{"type": "text", "text": text}] (list format)
        - AI messages: content = text (string format)
    """
    content = message.content

    # Handle string format (AI messages)
    if isinstance(content, str):
        return content

    # Handle list format (User messages)
    if isinstance(content, list) and len(content) > 0:
        # Extract text from first content block that has 'text' field
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and "text" in item:
                return item["text"]
        # If no text found, return empty string (e.g., image-only messages)
        return ""

    # Handle empty list or other formats
    if isinstance(content, list):
        return ""

    # Fallback for any other format
    return str(content)