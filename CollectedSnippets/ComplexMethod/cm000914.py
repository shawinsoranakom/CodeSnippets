async def _restore_cli_session_for_turn(
    user_id: str | None,
    session_id: str,
    session: "ChatSession",
    sdk_cwd: str,
    transcript_builder: "TranscriptBuilder",
    log_prefix: str,
) -> _RestoreResult:
    """Download, validate and restore a CLI session for ``--resume`` on this turn.

    Performs a single GCS round-trip to fetch the session bytes + message_count
    watermark.  Falls back to DB-message reconstruction when GCS has no session
    (first turn or upload missed).

    Returns a ``_RestoreResult`` with all transcript-related state ready for the
    caller to merge into its local variables.
    """
    result = _RestoreResult()

    if not (config.claude_agent_use_resume and user_id and len(session.messages) > 1):
        return result

    try:
        cli_restore = await download_transcript(
            user_id, session_id, log_prefix=log_prefix
        )
    except Exception as restore_err:
        logger.warning(
            "%s CLI session restore failed, continuing without --resume: %s",
            log_prefix,
            restore_err,
        )
        cli_restore = None

    # Only attempt --resume for SDK-written transcripts.
    # Baseline-written transcripts use TranscriptBuilder format (synthetic IDs,
    # stripped fields) that may not be valid for --resume.
    if cli_restore is not None and cli_restore.mode != "sdk":
        logger.info(
            "%s Transcript written by mode=%r — skipping --resume, "
            "will use transcript content + gap for context",
            log_prefix,
            cli_restore.mode,
        )
        result.baseline_download = cli_restore  # keep for extract_context_messages
        cli_restore = None

    # Validate, strip, and write to disk — delegate to helper to reduce
    # function complexity.  Writing an invalid/corrupt file to disk then
    # falling back to "no --resume" would cause the CLI to fail with
    # "Session ID already in use" because the file exists at the expected
    # session path, so we validate BEFORE any disk write.
    stripped = ""
    if cli_restore is not None and sdk_cwd:
        stripped, ok = process_cli_restore(cli_restore, sdk_cwd, session_id, log_prefix)
        if not ok:
            result.transcript_covers_prefix = False
            cli_restore = None

    if cli_restore is None and sdk_cwd:
        # Validation failed or GCS returned no session.  Delete any
        # existing local session file so the CLI doesn't reject the
        # session_id with "Session ID already in use".  T1 may have
        # left a valid file at this path; we clear it so the fallback
        # path (session_id= without --resume) can create a new session.
        _stale_path = os.path.realpath(cli_session_path(sdk_cwd, session_id))
        if Path(_stale_path).exists() and _stale_path.startswith(
            projects_base() + os.sep
        ):
            try:
                Path(_stale_path).unlink()
                logger.debug(
                    "%s Removed stale local CLI session file for clean fallback",
                    log_prefix,
                )
            except OSError as _unlink_err:
                logger.debug(
                    "%s Failed to remove stale local session file: %s",
                    log_prefix,
                    _unlink_err,
                )

    if cli_restore is not None:
        result.transcript_content = stripped
        transcript_builder.load_previous(stripped, log_prefix=log_prefix)
        result.use_resume = True
        result.resume_file = session_id
        result.transcript_msg_count = cli_restore.message_count
        return result

    # No valid --resume source (mode="baseline" or no GCS file).
    # Build context from transcript content + gap, falling back to full DB.
    # extract_context_messages handles both: non-None baseline_download uses
    # the compacted transcript + gap; None falls back to all prior DB messages.
    context_msgs = extract_context_messages(result.baseline_download, session.messages)
    result.context_messages = context_msgs
    result.transcript_msg_count = (
        result.baseline_download.message_count
        if result.baseline_download is not None
        and result.baseline_download.message_count > 0
        else len(session.messages) - 1
    )
    result.transcript_covers_prefix = True
    logger.info(
        "%s Context built from %s: %d messages (transcript watermark=%d, "
        "will inject as <conversation_history>)",
        log_prefix,
        (
            "baseline transcript + gap"
            if result.baseline_download is not None
            else "DB fallback"
        ),
        len(context_msgs),
        result.transcript_msg_count,
    )

    # Load baseline transcript content into builder so the upload path has accurate state.
    # Also sets result.transcript_content so the _seed_transcript guard in the caller
    # (``not transcript_content``) does not overwrite this builder state with a DB
    # reconstruction — which would duplicate entries since load_previous appends.
    if result.baseline_download is not None:
        try:
            raw_for_builder = result.baseline_download.content
            if isinstance(raw_for_builder, bytes):
                raw_for_builder = raw_for_builder.decode("utf-8")
            stripped = strip_for_upload(raw_for_builder)
            if validate_transcript(stripped):
                transcript_builder.load_previous(stripped, log_prefix=log_prefix)
                result.transcript_content = stripped
        except (UnicodeDecodeError, ValueError, OSError) as _load_err:
            # UnicodeDecodeError: non-UTF-8 content; ValueError: malformed JSONL in
            # strip_for_upload; OSError: encode/decode I/O failure.  Unexpected
            # exceptions propagate so programming errors are not silently masked.
            logger.debug(
                "%s Could not load baseline transcript into builder: %s",
                log_prefix,
                _load_err,
            )

    return result