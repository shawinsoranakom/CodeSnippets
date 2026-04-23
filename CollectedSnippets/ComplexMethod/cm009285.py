def _format_message_content(content: Any) -> Any:
    """Format message content for OpenRouter API.

    Converts LangChain data content blocks to the expected format.

    Args:
        content: The message content (string or list of content blocks).

    Returns:
        Formatted content suitable for the OpenRouter API.
    """
    if content and isinstance(content, list):
        formatted: list = []
        for block in content:
            if isinstance(block, dict) and is_data_content_block(block):
                if block.get("type") == "video":
                    formatted.append(_convert_video_block_to_openrouter(block))
                elif block.get("type") == "file":
                    formatted.append(_convert_file_block_to_openrouter(block))
                else:
                    formatted.append(convert_to_openai_data_block(block))
            else:
                formatted.append(block)
        return formatted
    return content