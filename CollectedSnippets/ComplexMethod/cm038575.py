def _parse_chat_message_content_mm_part(
    part: ChatCompletionContentPartParam,
) -> tuple[str, _ContentPart]:
    """
    Parses a given multi-modal content part based on its type.

    Args:
        part: A dict containing the content part, with a potential 'type' field.

    Returns:
        A tuple (part_type, content) where:
        - part_type: Type of the part (e.g., 'text', 'image_url').
        - content: Parsed content (e.g., text, image URL).

    Raises:
        ValueError: If the 'type' field is missing and no direct URL is found.
    """
    assert isinstance(
        part, dict
    )  # This is needed to avoid mypy errors: part.get() from str
    part_type = part.get("type", None)
    uuid = part.get("uuid", None)

    if isinstance(part_type, str) and part_type in MM_PARSER_MAP and uuid is None:  # noqa: E501
        content = MM_PARSER_MAP[part_type](part)

        # Special case for 'image_url.detail'
        # We only support 'auto', which is the default
        if part_type == "image_url" and part.get("detail", "auto") != "auto":
            logger.warning(
                "'image_url.detail' is currently not supported and will be ignored."
            )

        return part_type, content

    # Handle missing 'type' but provided direct URL fields.
    # 'type' is required field by pydantic
    if part_type is None or uuid is not None:
        if "image_url" in part:
            image_params = cast(CustomChatCompletionContentSimpleImageParam, part)
            image_url = image_params.get("image_url", None)
            if isinstance(image_url, dict):
                # Can potentially happen if user provides a uuid
                # with url as a dict of {"url": url}
                image_url = image_url.get("url", None)
            return "image_url", image_url
        if "image_pil" in part:
            # "image_pil" could be None if UUID is provided.
            image_params = cast(  # type: ignore
                CustomChatCompletionContentPILImageParam, part
            )
            image_pil = image_params.get("image_pil", None)
            return "image_pil", image_pil
        if "image_embeds" in part:
            # "image_embeds" could be None if UUID is provided.
            image_params = cast(  # type: ignore
                ChatCompletionContentPartImageEmbedsParam, part
            )
            image_embeds = image_params.get("image_embeds", None)
            return "image_embeds", image_embeds
        if "audio_embeds" in part:
            # "audio_embeds" could be None if UUID is provided.
            audio_params = cast(  # type: ignore[assignment]
                ChatCompletionContentPartAudioEmbedsParam, part
            )
            audio_embeds = audio_params.get("audio_embeds", None)
            return "audio_embeds", audio_embeds
        if "audio_url" in part:
            audio_params = cast(  # type: ignore[assignment]
                CustomChatCompletionContentSimpleAudioParam, part
            )
            audio_url = audio_params.get("audio_url", None)
            if isinstance(audio_url, dict):
                # Can potentially happen if user provides a uuid
                # with url as a dict of {"url": url}
                audio_url = audio_url.get("url", None)
            return "audio_url", audio_url
        if part.get("input_audio") is not None:
            input_audio_params = cast(dict[str, str], part)
            return "input_audio", input_audio_params
        if "video_url" in part:
            video_params = cast(CustomChatCompletionContentSimpleVideoParam, part)
            video_url = video_params.get("video_url", None)
            if isinstance(video_url, dict):
                # Can potentially happen if user provides a uuid
                # with url as a dict of {"url": url}
                video_url = video_url.get("url", None)
            return "video_url", video_url
        # Raise an error if no 'type' or direct URL is found.
        raise ValueError("Missing 'type' field in multimodal part.")

    if not isinstance(part_type, str):
        raise ValueError("Invalid 'type' field in multimodal part.")
    return part_type, "unknown part_type content"