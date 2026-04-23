def create_video_block(
    *,
    url: str | None = None,
    base64: str | None = None,
    file_id: str | None = None,
    mime_type: str | None = None,
    id: str | None = None,
    index: int | str | None = None,
    **kwargs: Any,
) -> VideoContentBlock:
    """Create a `VideoContentBlock`.

    Args:
        url: URL of the video.
        base64: Base64-encoded video data.
        file_id: ID of the video file from a file storage system.
        mime_type: MIME type of the video.

            Required for base64 data.
        id: Content block identifier.

            Generated automatically if not provided.
        index: Index of block in aggregate response.

            Used during streaming.

    Returns:
        A properly formatted `VideoContentBlock`.

    Raises:
        ValueError: If no video source is provided or if `base64` is used without
            `mime_type`.

    !!! note

        The `id` is generated automatically if not provided, using a UUID4 format
        prefixed with `'lc_'` to indicate it is a LangChain-generated ID.
    """
    if not any([url, base64, file_id]):
        msg = "Must provide one of: url, base64, or file_id"
        raise ValueError(msg)

    if base64 and not mime_type:
        msg = "mime_type is required when using base64 data"
        raise ValueError(msg)

    block = VideoContentBlock(type="video", id=ensure_id(id))

    if url is not None:
        block["url"] = url
    if base64 is not None:
        block["base64"] = base64
    if file_id is not None:
        block["file_id"] = file_id
    if mime_type is not None:
        block["mime_type"] = mime_type
    if index is not None:
        block["index"] = index

    extras = {k: v for k, v in kwargs.items() if v is not None}
    if extras:
        block["extras"] = extras

    return block