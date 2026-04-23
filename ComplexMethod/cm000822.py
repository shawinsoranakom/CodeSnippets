async def compact_transcript(
    content: str,
    *,
    model: str,
    log_prefix: str = "[Transcript]",
) -> str | None:
    """Compact an oversized JSONL transcript using LLM summarization.

    Converts transcript entries to plain messages, runs ``compress_context``
    (the same compressor used for pre-query history), and rebuilds JSONL.

    The **last assistant entry** (and any entries after it) are preserved
    verbatim — never flattened or compressed.  The Anthropic API requires
    ``thinking`` and ``redacted_thinking`` blocks in the latest assistant
    message to be value-identical to the original response (the API
    validates parsed signature values, not raw JSON bytes); compressing
    them would destroy the cryptographic signatures and cause
    ``invalid_request_error``.

    Structured content in *older* assistant entries (``tool_use`` blocks,
    ``thinking`` blocks, ``tool_result`` nesting, images) is flattened to
    plain text for compression.  This matches the fidelity of the Plan C
    (DB compression) fallback path.

    Returns the compacted JSONL string, or ``None`` on failure.

    See also:
        ``_compress_messages`` in ``service.py`` — compresses ``ChatMessage``
        lists for pre-query DB history.
    """
    prefix_lines, tail_lines = _find_last_assistant_entry(content)

    # Build the JSONL string for the compressible prefix
    prefix_content = "\n".join(prefix_lines) + "\n" if prefix_lines else ""
    messages = _transcript_to_messages(prefix_content) if prefix_content else []

    if len(messages) + len(tail_lines) < 2:
        total = len(messages) + len(tail_lines)
        logger.warning("%s Too few messages to compact (%d)", log_prefix, total)
        return None
    if not messages:
        logger.warning("%s Nothing to compress (only tail entries remain)", log_prefix)
        return None
    try:
        result = await _run_compression(messages, model, log_prefix)
        if not result.was_compacted:
            logger.warning(
                "%s Compressor reports within budget but SDK rejected — "
                "signalling failure",
                log_prefix,
            )
            return None
        if not result.messages:
            logger.warning("%s Compressor returned empty messages", log_prefix)
            return None
        logger.info(
            "%s Compacted transcript: %d->%d tokens (%d summarized, %d dropped)",
            log_prefix,
            result.original_token_count,
            result.token_count,
            result.messages_summarized,
            result.messages_dropped,
        )
        compressed_part = _messages_to_transcript(result.messages)

        # Re-append the preserved tail (last assistant + trailing entries)
        # with parentUuid patched to chain onto the compressed prefix.
        tail_part = _rechain_tail(compressed_part, tail_lines)
        compacted = compressed_part + tail_part

        if len(compacted) >= len(content):
            # Byte count can increase due to preserved tail entries
            # (thinking blocks, JSON overhead) even when token count
            # decreased.  Log a warning but still return — the API
            # validates tokens not bytes, and the caller falls through
            # to DB fallback if the transcript is still too large.
            logger.warning(
                "%s Compacted transcript (%d bytes) is not smaller than "
                "original (%d bytes) — may still reduce token count",
                log_prefix,
                len(compacted),
                len(content),
            )
        # Authoritative validation — the caller (_reduce_context) also
        # validates, but this is the canonical check that guarantees we
        # never return a malformed transcript from this function.
        if not validate_transcript(compacted):
            logger.warning("%s Compacted transcript failed validation", log_prefix)
            return None
        return compacted
    except Exception as e:
        logger.error(
            "%s Transcript compaction failed: %s", log_prefix, e, exc_info=True
        )
        return None