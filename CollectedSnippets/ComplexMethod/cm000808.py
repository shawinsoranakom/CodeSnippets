async def get_active_session(
    session_id: str,
    user_id: str | None = None,
) -> tuple[ActiveSession | None, str]:
    """Get the active (running) session, if any.

    Direct O(1) lookup by session_id.

    Args:
        session_id: Session ID to look up
        user_id: User ID for ownership validation (optional)

    Returns:
        Tuple of (ActiveSession if found and running, last_message_id from Redis Stream)
    """

    redis = await get_redis_async()
    meta_key = _get_session_meta_key(session_id)
    meta: dict[Any, Any] = await redis.hgetall(meta_key)  # type: ignore[misc]

    if not meta:
        return None, "0-0"

    session_status = meta.get("status", "")
    session_user_id = meta.get("user_id", "") or None

    if session_status != "running":
        return None, "0-0"

    # Validate ownership - if session has an owner, requester must match
    if session_user_id and user_id != session_user_id:
        return None, "0-0"

    # Check if session is stale (running beyond tool timeout + buffer).
    # Auto-complete it to prevent infinite polling loops.
    # A turn can legitimately run up to COPILOT_CONSUMER_TIMEOUT_SECONDS, so we
    # add a 5-minute buffer to avoid false positives during legitimate operations.
    created_at_str = meta.get("created_at")
    if created_at_str:
        try:
            created_at = datetime.fromisoformat(created_at_str)
            age_seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
            stale_threshold = COPILOT_CONSUMER_TIMEOUT_SECONDS + 300  # + 5min buffer
            if age_seconds > stale_threshold:
                logger.warning(
                    f"[STALE_SESSION] Auto-completing stale session {session_id[:8]}... "
                    f"(running for {age_seconds:.0f}s, threshold: {stale_threshold}s)"
                )
                await mark_session_completed(
                    session_id,
                    error_message=f"Session timed out after {age_seconds:.0f}s",
                )
                return None, "0-0"
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse created_at: {e}")

    session = _parse_session_meta(meta, session_id)
    logger.info(
        f"[SESSION_LOOKUP] Found running session {session_id[:8]}..., turn_id={session.turn_id[:8]}"
    )

    # Get the last message ID from Redis Stream (keyed by turn_id)
    stream_key = _get_turn_stream_key(session.turn_id)
    last_id = "0-0"
    try:
        messages = await redis.xrevrange(stream_key, count=1)
        if messages:
            msg_id = messages[0][0]
            last_id = msg_id if isinstance(msg_id, str) else msg_id.decode()
    except Exception as e:
        logger.warning(f"Failed to get last message ID: {e}")

    return session, last_id