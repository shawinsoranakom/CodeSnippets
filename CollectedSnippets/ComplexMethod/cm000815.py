async def download_transcript(
    user_id: str,
    session_id: str,
    log_prefix: str = "[Transcript]",
) -> TranscriptDownload | None:
    """Download CLI session from GCS. Returns content + message_count + mode, or None if not found.

    Pure GCS operation — no disk I/O.  The caller is responsible for writing
    content to disk if --resume is needed.

    Returns a TranscriptDownload with the raw content, message_count watermark,
    and mode on success, or None if not available (first turn or upload failed).
    """
    storage = await get_workspace_storage()
    path = _build_path_from_parts(
        _cli_session_storage_path_parts(user_id, session_id), storage
    )
    meta_path = _build_path_from_parts(
        _cli_session_meta_path_parts(user_id, session_id), storage
    )

    content_result, meta_result = await asyncio.gather(
        storage.retrieve(path),
        storage.retrieve(meta_path),
        return_exceptions=True,
    )

    if isinstance(content_result, FileNotFoundError):
        logger.debug("%s No CLI session in storage (first turn or missing)", log_prefix)
        return None
    if isinstance(content_result, BaseException):
        logger.warning(
            "%s Failed to download CLI session: %s", log_prefix, content_result
        )
        return None

    content: bytes = content_result

    # Parse message_count and mode from companion meta — best-effort, defaults.
    message_count = 0
    mode: TranscriptMode = "sdk"
    if isinstance(meta_result, FileNotFoundError):
        pass  # No meta — old upload; default to "sdk"
    elif isinstance(meta_result, BaseException):
        logger.debug("%s Failed to load CLI session meta: %s", log_prefix, meta_result)
    else:
        try:
            meta_str = meta_result.decode("utf-8")
        except UnicodeDecodeError:
            logger.debug("%s CLI session meta is not valid UTF-8, ignoring", log_prefix)
            meta_str = None
        if meta_str is not None:
            meta = json.loads(meta_str, fallback={})
            if isinstance(meta, dict):
                raw_count = meta.get("message_count", 0)
                message_count = (
                    raw_count if isinstance(raw_count, int) and raw_count >= 0 else 0
                )
                raw_mode = meta.get("mode", "sdk")
                mode = raw_mode if raw_mode in ("sdk", "baseline") else "sdk"

    logger.info(
        "%s Downloaded CLI session (%dB, msg_count=%d, mode=%s)",
        log_prefix,
        len(content),
        message_count,
        mode,
    )
    return TranscriptDownload(content=content, message_count=message_count, mode=mode)