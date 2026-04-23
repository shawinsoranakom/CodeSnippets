def _convert_to_v1_from_chat_completions_input(
    content: list[types.ContentBlock],
) -> list[types.ContentBlock]:
    """Convert OpenAI Chat Completions format blocks to v1 format.

    During the `content_blocks` parsing process, we wrap blocks not recognized as a v1
    block as a `'non_standard'` block with the original block stored in the `value`
    field. This function attempts to unpack those blocks and convert any blocks that
    might be OpenAI format to v1 ContentBlocks.

    If conversion fails, the block is left as a `'non_standard'` block.

    Args:
        content: List of content blocks to process.

    Returns:
        Updated list with OpenAI blocks converted to v1 format.
    """
    converted_blocks = []
    unpacked_blocks: list[dict[str, Any]] = [
        cast("dict[str, Any]", block)
        if block.get("type") != "non_standard"
        else block["value"]  # type: ignore[typeddict-item]  # this is only non-standard blocks
        for block in content
    ]
    for block in unpacked_blocks:
        if block.get("type") in {
            "image_url",
            "input_audio",
            "file",
        } and is_openai_data_block(block):
            converted_block = _convert_openai_format_to_data_block(block)
            # If conversion succeeded, use it; otherwise keep as non_standard
            if (
                isinstance(converted_block, dict)
                and converted_block.get("type") in types.KNOWN_BLOCK_TYPES
            ):
                converted_blocks.append(cast("types.ContentBlock", converted_block))
            else:
                converted_blocks.append({"type": "non_standard", "value": block})
        elif block.get("type") in types.KNOWN_BLOCK_TYPES:
            converted_blocks.append(cast("types.ContentBlock", block))
        else:
            converted_blocks.append({"type": "non_standard", "value": block})

    return converted_blocks