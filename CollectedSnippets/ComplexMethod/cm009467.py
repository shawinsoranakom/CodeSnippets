def is_openai_data_block(
    block: dict, filter_: Literal["image", "audio", "file"] | None = None
) -> bool:
    """Check whether a block contains multimodal data in OpenAI Chat Completions format.

    Supports both data and ID-style blocks (e.g. `'file_data'` and `'file_id'`)

    If additional keys are present, they are ignored / will not affect outcome as long
    as the required keys are present and valid.

    Args:
        block: The content block to check.
        filter_: If provided, only return True for blocks matching this specific type.
            - "image": Only match image_url blocks
            - "audio": Only match input_audio blocks
            - "file": Only match file blocks
            If `None`, match any valid OpenAI data block type. Note that this means that
            if the block has a valid OpenAI data type but the filter_ is set to a
            different type, this function will return False.

    Returns:
        `True` if the block is a valid OpenAI data block and matches the filter_
        (if provided).

    """
    if block.get("type") == "image_url":
        if filter_ is not None and filter_ != "image":
            return False
        if (
            (set(block.keys()) <= {"type", "image_url", "detail"})
            and (image_url := block.get("image_url"))
            and isinstance(image_url, dict)
        ):
            url = image_url.get("url")
            if isinstance(url, str):
                # Required per OpenAI spec
                return True
            # Ignore `'detail'` since it's optional and specific to OpenAI

    elif block.get("type") == "input_audio":
        if filter_ is not None and filter_ != "audio":
            return False
        if (audio := block.get("input_audio")) and isinstance(audio, dict):
            audio_data = audio.get("data")
            audio_format = audio.get("format")
            # Both required per OpenAI spec
            if isinstance(audio_data, str) and isinstance(audio_format, str):
                return True

    elif block.get("type") == "file":
        if filter_ is not None and filter_ != "file":
            return False
        if (file := block.get("file")) and isinstance(file, dict):
            file_data = file.get("file_data")
            file_id = file.get("file_id")
            # Files can be either base64-encoded or pre-uploaded with an ID
            if isinstance(file_data, str) or isinstance(file_id, str):
                return True

    else:
        return False

    # Has no `'type'` key
    return False