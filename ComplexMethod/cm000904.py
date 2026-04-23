def read_cli_session_from_disk(
    sdk_cwd: str,
    session_id: str,
    log_prefix: str,
) -> bytes | None:
    """Read the CLI session JSONL file from disk after the SDK turn.

    Returns the file bytes, or None if the file is missing, outside the
    projects base, or unreadable.
    Path-traversal guard: rejects paths outside the CLI projects base.
    """
    session_file = cli_session_path(sdk_cwd, session_id)
    real_path = os.path.realpath(session_file)
    _pbase = projects_base()
    if not real_path.startswith(_pbase + os.sep):
        logger.warning(
            "%s CLI session file outside projects base, skipping upload: %s",
            log_prefix,
            os.path.basename(real_path),
        )
        return None
    try:
        raw_bytes = Path(real_path).read_bytes()
    except FileNotFoundError:
        logger.debug(
            "%s CLI session file not found, skipping upload: %s",
            log_prefix,
            os.path.basename(session_file),
        )
        return None
    except OSError as e:
        logger.warning(
            "%s Failed to read CLI session file %s: %s",
            log_prefix,
            os.path.basename(session_file),
            e.strerror or str(e),
        )
        return None

    # Strip stale thinking blocks and metadata entries before uploading.
    # Thinking blocks from non-last turns can be massive; keeping them causes
    # the CLI to auto-compact its session when the context window fills up,
    # silently losing conversation history.
    try:
        raw_text = raw_bytes.decode("utf-8")
        stripped_text = strip_for_upload(raw_text)
        stripped_bytes = stripped_text.encode("utf-8")
    except UnicodeDecodeError:
        logger.warning("%s CLI session is not valid UTF-8, uploading raw", log_prefix)
        return raw_bytes
    except (OSError, ValueError) as e:
        # OSError: encode/decode I/O failure; ValueError: malformed JSONL in strip.
        # Other unexpected exceptions are not silently swallowed here so they propagate
        # to the outer OSError handler and are logged with exc_info.
        logger.warning(
            "%s Failed to strip CLI session, uploading raw: %s", log_prefix, e
        )
        return raw_bytes

    if len(stripped_bytes) < len(raw_bytes):
        # Write back locally so same-pod turns also benefit.
        try:
            Path(real_path).write_bytes(stripped_bytes)
            logger.info(
                "%s Stripped CLI session: %dB → %dB",
                log_prefix,
                len(raw_bytes),
                len(stripped_bytes),
            )
        except OSError as e:
            # write_bytes failed — stripped content is still valid for GCS upload even
            # though the local write-back failed (same-pod optimization silently skipped).
            logger.warning(
                "%s Failed to write back stripped CLI session: %s",
                log_prefix,
                e.strerror or str(e),
            )
    return stripped_bytes