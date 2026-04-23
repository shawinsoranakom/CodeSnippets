def _convert_openai_format_to_data_block(
    block: dict,
) -> types.ContentBlock | dict[Any, Any]:
    """Convert OpenAI image/audio/file content block to respective v1 multimodal block.

    We expect that the incoming block is verified to be in OpenAI Chat Completions
    format.

    If parsing fails, passes block through unchanged.

    Mappings (Chat Completions to LangChain v1):
    - Image -> `ImageContentBlock`
    - Audio -> `AudioContentBlock`
    - File -> `FileContentBlock`

    """

    # Extract extra keys to put them in `extras`
    def _extract_extras(block_dict: dict, known_keys: set[str]) -> dict[str, Any]:
        """Extract unknown keys from block to preserve as extras."""
        return {k: v for k, v in block_dict.items() if k not in known_keys}

    # base64-style image block
    if (block["type"] == "image_url") and (
        parsed := _parse_data_uri(block["image_url"]["url"])
    ):
        known_keys = {"type", "image_url"}
        extras = _extract_extras(block, known_keys)

        # Also extract extras from nested image_url dict
        image_url_known_keys = {"url"}
        image_url_extras = _extract_extras(block["image_url"], image_url_known_keys)

        # Merge extras
        all_extras = {**extras}
        for key, value in image_url_extras.items():
            if key == "detail":  # Don't rename
                all_extras["detail"] = value
            else:
                all_extras[f"image_url_{key}"] = value

        return types.create_image_block(
            # Even though this is labeled as `url`, it can be base64-encoded
            base64=parsed["data"],
            mime_type=parsed["mime_type"],
            **all_extras,
        )

    # url-style image block
    if (block["type"] == "image_url") and isinstance(
        block["image_url"].get("url"), str
    ):
        known_keys = {"type", "image_url"}
        extras = _extract_extras(block, known_keys)

        image_url_known_keys = {"url"}
        image_url_extras = _extract_extras(block["image_url"], image_url_known_keys)

        all_extras = {**extras}
        for key, value in image_url_extras.items():
            if key == "detail":  # Don't rename
                all_extras["detail"] = value
            else:
                all_extras[f"image_url_{key}"] = value

        return types.create_image_block(
            url=block["image_url"]["url"],
            **all_extras,
        )

    # base64-style audio block
    # audio is only represented via raw data, no url or ID option
    if block["type"] == "input_audio":
        known_keys = {"type", "input_audio"}
        extras = _extract_extras(block, known_keys)

        # Also extract extras from nested audio dict
        audio_known_keys = {"data", "format"}
        audio_extras = _extract_extras(block["input_audio"], audio_known_keys)

        all_extras = {**extras}
        for key, value in audio_extras.items():
            all_extras[f"audio_{key}"] = value

        return types.create_audio_block(
            base64=block["input_audio"]["data"],
            mime_type=f"audio/{block['input_audio']['format']}",
            **all_extras,
        )

    # id-style file block
    if block.get("type") == "file" and "file_id" in block.get("file", {}):
        known_keys = {"type", "file"}
        extras = _extract_extras(block, known_keys)

        file_known_keys = {"file_id"}
        file_extras = _extract_extras(block["file"], file_known_keys)

        all_extras = {**extras}
        for key, value in file_extras.items():
            all_extras[f"file_{key}"] = value

        return types.create_file_block(
            file_id=block["file"]["file_id"],
            **all_extras,
        )

    # base64-style file block
    if (block["type"] == "file") and (
        parsed := _parse_data_uri(block["file"]["file_data"])
    ):
        known_keys = {"type", "file"}
        extras = _extract_extras(block, known_keys)

        file_known_keys = {"file_data", "filename"}
        file_extras = _extract_extras(block["file"], file_known_keys)

        all_extras = {**extras}
        for key, value in file_extras.items():
            all_extras[f"file_{key}"] = value

        filename = block["file"].get("filename")
        return types.create_file_block(
            base64=parsed["data"],
            mime_type="application/pdf",
            filename=filename,
            **all_extras,
        )

    # Escape hatch
    return block