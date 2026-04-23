def create_plaintext_block(
    text: str | None = None,
    url: str | None = None,
    base64: str | None = None,
    file_id: str | None = None,
    title: str | None = None,
    context: str | None = None,
    id: str | None = None,
    index: int | str | None = None,
    **kwargs: Any,
) -> PlainTextContentBlock:
    """Create a `PlainTextContentBlock`.

    Args:
        text: The plaintext content.
        url: URL of the plaintext file.
        base64: Base64-encoded plaintext data.
        file_id: ID of the plaintext file from a file storage system.
        title: Title of the text data.
        context: Context or description of the text content.
        id: Content block identifier.

            Generated automatically if not provided.
        index: Index of block in aggregate response.

            Used during streaming.

    Returns:
        A properly formatted `PlainTextContentBlock`.

    !!! note

        The `id` is generated automatically if not provided, using a UUID4 format
        prefixed with `'lc_'` to indicate it is a LangChain-generated ID.
    """
    block = PlainTextContentBlock(
        type="text-plain",
        mime_type="text/plain",
        id=ensure_id(id),
    )

    if text is not None:
        block["text"] = text
    if url is not None:
        block["url"] = url
    if base64 is not None:
        block["base64"] = base64
    if file_id is not None:
        block["file_id"] = file_id
    if title is not None:
        block["title"] = title
    if context is not None:
        block["context"] = context
    if index is not None:
        block["index"] = index

    extras = {k: v for k, v in kwargs.items() if v is not None}
    if extras:
        block["extras"] = extras

    return block