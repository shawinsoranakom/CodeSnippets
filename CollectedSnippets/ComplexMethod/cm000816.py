def extract_context_messages(
    download: TranscriptDownload | None,
    session_messages: "list[ChatMessage]",
) -> "list[ChatMessage]":
    """Return context messages for the current turn: transcript content + gap.

    This is the shared context primitive used by both the SDK path
    (``use_resume=False`` → ``<conversation_history>`` injection) and the
    baseline path (OpenAI messages array).

    How it works:

    - When a transcript exists, ``TranscriptBuilder.load_previous`` preserves
      ``isCompactSummary=True`` compaction entries, so the returned messages
      mirror the compacted context the CLI would see via ``--resume``.
    - The gap (DB messages after the transcript watermark) is always small in
      normal operation; it only grows during mode switches or when an upload
      was missed.
    - Falls back to full DB messages when no transcript exists (first turn,
      upload failure, or GCS unavailable).
    - Returns *prior* messages only (excluding the current user turn at
      ``session_messages[-1]``).  Callers that need the current turn append
      ``session_messages[-1]`` themselves.
    - **Tool calls from transcript entries are flattened to text**: assistant
      messages derived from the JSONL use ``_flatten_assistant_content``, which
      serialises ``tool_use`` blocks as human-readable text rather than
      structured ``tool_calls``.  Gap messages (from DB) preserve their
      original ``tool_calls`` field.  This is the same trade-off as the old
      ``_compress_session_messages(session.messages)`` approach — no regression.

    Args:
        download: The ``TranscriptDownload`` from GCS, or ``None`` when no
            transcript is available.  ``content`` may be either ``bytes`` or
            ``str`` (the baseline path decodes + strips before returning).
        session_messages: All messages in the session, with the current user
            turn as the last element.

    Returns:
        A list of ``ChatMessage`` objects covering the prior conversation
        context, suitable for injection as conversation history.
    """
    from .model import ChatMessage as _ChatMessage  # runtime import

    # ``role="reasoning"`` rows are persisted for frontend replay of
    # extended_thinking content but are NOT conversation context — the
    # transcript-based --resume path already carries thinking separately,
    # and sending them back to the model as user/assistant turns would be
    # both redundant and malformed.  Drop them before any gap detection
    # or transcript comparison so ordering invariants still hold.
    session_messages = [m for m in session_messages if m.role != "reasoning"]

    prior = session_messages[:-1]

    if download is None:
        return prior

    raw_content = download.content
    if not raw_content:
        return prior

    # Handle both bytes (raw GCS download) and str (pre-decoded baseline path).
    if isinstance(raw_content, bytes):
        try:
            content_str: str = raw_content.decode("utf-8")
        except UnicodeDecodeError:
            return prior
    else:
        content_str = raw_content

    raw = _transcript_to_messages(content_str)
    if not raw:
        return prior

    transcript_msgs = [
        _ChatMessage(role=m["role"], content=m.get("content") or "") for m in raw
    ]
    gap = detect_gap(download, session_messages)
    return transcript_msgs + gap