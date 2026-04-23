async def _load_prior_transcript(
    user_id: str,
    session_id: str,
    session_messages: list[ChatMessage],
    transcript_builder: TranscriptBuilder,
) -> tuple[bool, "TranscriptDownload | None"]:
    """Download and load the prior CLI session into ``transcript_builder``.

    Returns a tuple of (upload_safe, transcript_download):
    - ``upload_safe`` is ``True`` when it is safe to upload at the end of this
      turn.  Upload is suppressed only for **download errors** (unknown GCS
      state) — missing and invalid files return ``True`` because there is
      nothing in GCS worth protecting against overwriting.
    - ``transcript_download`` is a ``TranscriptDownload`` with str content
      (pre-decoded and stripped) when available, or ``None`` when no valid
      transcript could be loaded.  Callers pass this to
      ``extract_context_messages`` to build the LLM context.
    """
    try:
        restore = await download_transcript(
            user_id, session_id, log_prefix="[Baseline]"
        )
    except Exception as e:
        logger.warning("[Baseline] Session restore failed: %s", e)
        # Unknown GCS state — be conservative, skip upload.
        return False, None

    if restore is None:
        logger.debug("[Baseline] No CLI session available — will upload fresh")
        # Nothing in GCS to protect; allow upload so the first baseline turn
        # writes the initial transcript snapshot.
        return True, None

    content_bytes = restore.content
    try:
        raw_str = (
            content_bytes.decode("utf-8")
            if isinstance(content_bytes, bytes)
            else content_bytes
        )
    except UnicodeDecodeError:
        logger.warning("[Baseline] CLI session content is not valid UTF-8")
        # Corrupt file in GCS; overwriting with a valid one is better.
        return True, None

    stripped = strip_for_upload(raw_str)
    if not validate_transcript(stripped):
        logger.warning("[Baseline] CLI session content invalid after strip")
        # Corrupt file in GCS; overwriting with a valid one is better.
        return True, None

    transcript_builder.load_previous(stripped, log_prefix="[Baseline]")
    logger.info(
        "[Baseline] Loaded CLI session: %dB, msg_count=%d",
        len(content_bytes) if isinstance(content_bytes, bytes) else len(raw_str),
        restore.message_count,
    )

    gap = detect_gap(restore, session_messages)
    if gap:
        _append_gap_to_builder(gap, transcript_builder)
        logger.info(
            "[Baseline] Filled gap: loaded %d transcript msgs + %d gap msgs from DB",
            restore.message_count,
            len(gap),
        )

    # Return a str-content version so extract_context_messages receives a
    # pre-decoded, stripped transcript (avoids redundant decode + strip).
    # TranscriptDownload.content is typed as bytes | str; we pass str here
    # to avoid a redundant encode + decode round-trip.
    str_restore = TranscriptDownload(
        content=stripped,
        message_count=restore.message_count,
        mode=restore.mode,
    )
    return True, str_restore