async def mark_session_completed(
    session_id: str,
    error_message: str | None = None,
    *,
    skip_error_publish: bool = False,
) -> bool:
    """Mark a session as completed, then publish StreamFinish.

    This is the SINGLE place that publishes StreamFinish to the turn stream.
    Services must NOT yield StreamFinish themselves — the processor intercepts
    it and calls this function instead, ensuring status is set before
    StreamFinish reaches the frontend.

    Uses atomic compare-and-swap via Lua script to prevent race conditions.
    Idempotent — calling multiple times is safe (returns False on no-op).

    Args:
        session_id: Session ID to mark as completed
        error_message: If provided, marks as "failed" and publishes a
            StreamError before StreamFinish. Otherwise marks as "completed".
        skip_error_publish: If True, still marks the session as "failed" but
            does NOT publish a StreamError event. Use this when the error has
            already been published to the stream (e.g. via stream_and_publish)
            to avoid duplicate error delivery to the frontend.

    Returns:
        True if session was newly marked completed, False if already completed/failed
    """
    status: Literal["completed", "failed"] = "failed" if error_message else "completed"
    redis = await get_redis_async()
    meta_key = _get_session_meta_key(session_id)

    # Resolve turn_id for publishing to the correct stream
    meta: dict[Any, Any] = await redis.hgetall(meta_key)  # type: ignore[misc]
    turn_id = _parse_session_meta(meta, session_id).turn_id if meta else session_id

    # Atomic compare-and-swap: only update if status is "running"
    swapped = await hash_compare_and_set(
        redis, meta_key, "status", expected="running", new=status
    )

    # Clean up the in-memory TTL refresh tracker to prevent unbounded growth.
    _meta_ttl_refresh_at.pop(session_id, None)

    if not swapped:
        logger.debug(f"Session {session_id} already completed/failed, skipping")
        return False

    # Force-release the executor's cluster lock so the next enqueued turn can
    # acquire it immediately. The lock holder's on_run_done will also release
    # (idempotent delete); doing it here unblocks cases where the task hangs
    # past the cancel timeout or a pod crash leaves the lock orphaned.
    try:
        await redis.delete(get_session_lock_key(session_id))
    except RedisError as e:
        logger.warning(f"Failed to release cluster lock for session {session_id}: {e}")

    if error_message and not skip_error_publish:
        try:
            await publish_chunk(turn_id, StreamError(errorText=error_message))
        except Exception as e:
            logger.warning(
                f"Failed to publish error event for session {session_id}: {e}"
            )

    # Compute wall-clock duration from session created_at.
    # Only persist when (a) the session completed successfully and
    # (b) created_at was actually present in Redis meta (not a fallback).
    duration_ms: int | None = None
    if meta and not error_message:
        created_at_raw = meta.get("created_at")
        if created_at_raw:
            try:
                created_at = datetime.fromisoformat(str(created_at_raw))
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                elapsed = datetime.now(timezone.utc) - created_at
                duration_ms = max(0, int(elapsed.total_seconds() * 1000))
            except (ValueError, TypeError):
                logger.warning(
                    "Failed to compute session duration for %s (created_at=%r)",
                    session_id,
                    created_at_raw,
                )

    # Persist duration on the last assistant message
    if duration_ms is not None:
        try:
            await chat_db().set_turn_duration(session_id, duration_ms)
        except Exception as e:
            logger.warning(f"Failed to save turn duration for {session_id}: {e}")

    # Publish StreamFinish AFTER status is set to "completed"/"failed".
    # This is the SINGLE place that publishes StreamFinish — services and
    # the processor must NOT publish it themselves.
    try:
        await publish_chunk(
            turn_id,
            StreamFinish(),
        )
    except Exception as e:
        logger.error(
            f"Failed to publish StreamFinish for session {session_id}: {e}. "
            "The _stream_listener will detect completion via status polling."
        )

    # Clean up local session reference if exists
    _local_sessions.pop(session_id, None)

    # Publish copilot completion notification via WebSocket
    if meta:
        parsed = _parse_session_meta(meta, session_id)
        if parsed.user_id:
            try:
                await _notification_bus.publish(
                    NotificationEvent(
                        user_id=parsed.user_id,
                        payload=CopilotCompletionPayload(
                            type="copilot_completion",
                            event="session_completed",
                            session_id=session_id,
                            status=status,
                        ),
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Failed to publish copilot completion notification "
                    f"for session {session_id}: {e}"
                )

    return True