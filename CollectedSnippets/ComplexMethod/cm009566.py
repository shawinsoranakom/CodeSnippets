def is_data_content_block(block: dict) -> bool:
    """Check if the provided content block is a data content block.

    Returns True for both v0 (old-style) and v1 (new-style) multimodal data blocks.

    Args:
        block: The content block to check.

    Returns:
        `True` if the content block is a data content block, `False` otherwise.
    """
    if block.get("type") not in _get_data_content_block_types():
        return False

    if any(key in block for key in ("url", "base64", "file_id", "text")):
        # Type is valid and at least one data field is present
        # (Accepts old-style image and audio URLContentBlock)

        # 'text' is checked to support v0 PlainTextContentBlock types
        # We must guard against new style TextContentBlock which also has 'text' `type`
        # by ensuring the presence of `source_type`
        if block["type"] == "text" and "source_type" not in block:  # noqa: SIM103  # This is more readable
            return False

        return True

    if "source_type" in block:
        # Old-style content blocks had possible types of 'image', 'audio', and 'file'
        # which is not captured in the prior check
        source_type = block["source_type"]
        if (source_type == "url" and "url" in block) or (
            source_type == "base64" and "data" in block
        ):
            return True
        if (source_type == "id" and "id" in block) or (
            source_type == "text" and "url" in block
        ):
            return True

    return False