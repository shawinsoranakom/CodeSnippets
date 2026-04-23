def _parse_chat_message_content_part(
    part: ChatCompletionContentPartParam,
    mm_parser: BaseMultiModalContentParser,
    *,
    wrap_dicts: bool,
    interleave_strings: bool,
) -> _ContentPart | None:
    """Parses a single part of a conversation. If wrap_dicts is True,
    structured dictionary pieces for texts and images will be
    wrapped in dictionaries, i.e., {"type": "text", "text", ...} and
    {"type": "image"}, respectively. Otherwise multimodal data will be
    handled by mm_parser, and texts will be returned as strings to be joined
    with multimodal placeholders.
    """
    if isinstance(part, str):  # Handle plain text parts
        if wrap_dicts:
            return {"type": "text", "text": part}
        return part
    # Handle structured dictionary parts
    part_type, content = _parse_chat_message_content_mm_part(part)
    # if part_type is text/refusal/image_url/audio_url/video_url/input_audio but
    # content is None, log a warning and skip
    if part_type in PART_TYPES_TO_SKIP_NONE_CONTENT and content is None:
        logger.warning(
            "Skipping multimodal part '%s' (type: '%s') "
            "with empty / unparsable content.",
            part,
            part_type,
        )
        return None

    if part_type in ("text", "input_text", "output_text", "refusal", "thinking"):
        str_content = cast(str, content)
        if wrap_dicts:
            return {"type": "text", "text": str_content}
        else:
            return str_content

    # For media items, if a user has provided one, use it. Otherwise, insert
    # a placeholder empty uuid.
    uuid = part.get("uuid", None)
    if uuid is not None:
        uuid = str(uuid)

    modality = None
    if part_type == "image_pil":
        image_content = cast(Image.Image, content) if content is not None else None
        mm_parser.parse_image_pil(image_content, uuid)
        modality = "image"
    elif part_type in ("image_url", "input_image"):
        str_content = cast(str, content)
        mm_parser.parse_image(str_content, uuid)
        modality = "image"
    elif part_type == "image_embeds":
        content = cast(str | dict[str, str], content) if content is not None else None
        mm_parser.parse_image_embeds(content, uuid)
        modality = "image"
    elif part_type == "audio_embeds":
        content = cast(str | dict[str, str], content) if content is not None else None
        mm_parser.parse_audio_embeds(content, uuid)
        modality = "audio"
    elif part_type == "audio_url":
        str_content = cast(str, content)
        mm_parser.parse_audio(str_content, uuid)
        modality = "audio"
    elif part_type == "input_audio":
        dict_content = cast(InputAudio, content)
        mm_parser.parse_input_audio(dict_content, uuid)
        modality = "audio"
    elif part_type == "video_url":
        str_content = cast(str, content)
        mm_parser.parse_video(str_content, uuid)
        modality = "video"
    else:
        raise NotImplementedError(f"Unknown part type: {part_type}")

    if wrap_dicts:
        return {"type": modality}
    return MODALITY_PLACEHOLDERS_MAP[modality] if interleave_strings else None