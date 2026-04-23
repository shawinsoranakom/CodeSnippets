async def enqueue_conversation_turn(
    user_id: str,
    session_id: str,
    user_msg: str,
    assistant_msg: str = "",
) -> None:
    """Enqueue a conversation turn for async background ingestion.

    This returns almost immediately — the actual graphiti-core
    ``add_episode()`` call (which triggers LLM entity extraction)
    runs in a background worker task.

    If ``assistant_msg`` is provided and contains substantive findings
    (not just acknowledgments), a separate derived-finding episode is
    queued with ``source_kind=assistant_derived`` and ``status=tentative``.
    """
    if not user_id:
        return

    try:
        group_id = derive_group_id(user_id)
    except ValueError:
        logger.warning("Invalid user_id for ingestion: %s", user_id[:12])
        return

    user_display_name = await _resolve_user_name(user_id)

    episode_name = f"conversation_{session_id}"

    # User's own words only, in graphiti's expected "Speaker: content" format.
    # Assistant response is excluded from extraction
    # (Zep Cloud approach: ignore_roles=["assistant"]).
    episode_body_for_graphiti = f"{user_display_name}: {user_msg}"

    source_description = f"User message in session {session_id}"

    queue = await _ensure_worker(user_id)

    try:
        queue.put_nowait(
            {
                "name": episode_name,
                "episode_body": episode_body_for_graphiti,
                "source": EpisodeType.message,
                "source_description": source_description,
                "reference_time": datetime.now(timezone.utc),
                "group_id": group_id,
                "custom_extraction_instructions": CUSTOM_EXTRACTION_INSTRUCTIONS,
            }
        )
    except asyncio.QueueFull:
        logger.warning(
            "Graphiti ingestion queue full for user %s — dropping episode",
            user_id[:12],
        )
        return

    # --- Derived-finding lane ---
    # If the assistant response is substantive, distill it into a
    # structured finding with tentative status.
    if assistant_msg and _is_finding_worthy(assistant_msg):
        finding = _distill_finding(assistant_msg)
        if finding:
            envelope = MemoryEnvelope(
                content=finding,
                source_kind=SourceKind.assistant_derived,
                memory_kind=MemoryKind.finding,
                status=MemoryStatus.tentative,
                provenance=f"session:{session_id}",
            )
            try:
                queue.put_nowait(
                    {
                        "name": f"finding_{session_id}",
                        "episode_body": envelope.model_dump_json(),
                        "source": EpisodeType.json,
                        "source_description": f"Assistant-derived finding in session {session_id}",
                        "reference_time": datetime.now(timezone.utc),
                        "group_id": group_id,
                        "custom_extraction_instructions": CUSTOM_EXTRACTION_INSTRUCTIONS,
                    }
                )
            except asyncio.QueueFull:
                pass