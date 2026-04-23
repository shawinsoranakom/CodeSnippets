async def _resolve_write_content(
    content_text: str | None,
    content_b64: str | None,
    source_path: str | None,
    session_id: str,
) -> bytes | ErrorResponse:
    """Resolve file content from exactly one of three input sources.

    Returns the raw bytes on success, or an ``ErrorResponse`` on validation
    failure (wrong number of sources, invalid path, file not found, etc.).

    When an E2B sandbox is active, ``source_path`` reads from the sandbox
    filesystem instead of the local ephemeral directory.
    """
    # Normalise empty strings to None so counting and dispatch stay in sync.
    if content_text is not None and content_text == "":
        content_text = None
    if content_b64 is not None and content_b64 == "":
        content_b64 = None
    if source_path is not None and source_path == "":
        source_path = None

    sources_provided = sum(
        x is not None for x in [content_text, content_b64, source_path]
    )
    if sources_provided == 0:
        return ErrorResponse(
            message="Please provide one of: content, content_base64, or source_path",
            session_id=session_id,
        )
    if sources_provided > 1:
        return ErrorResponse(
            message="Provide only one of: content, content_base64, or source_path",
            session_id=session_id,
        )

    if source_path is not None:
        return await _read_source_path(source_path, session_id)

    if content_b64 is not None:
        try:
            return base64.b64decode(content_b64)
        except Exception:
            return ErrorResponse(
                message=(
                    "Invalid base64 encoding in content_base64. "
                    "Please encode the file content with standard base64, "
                    "or use the 'content' parameter for plain text, "
                    "or 'source_path' to copy from the working directory."
                ),
                session_id=session_id,
            )

    assert content_text is not None
    return content_text.encode("utf-8")