async def subscribe_to_session(
    session_id: str,
    user_id: str | None,
    last_message_id: str = "0-0",
) -> asyncio.Queue[StreamBaseResponse] | None:
    """Subscribe to a session's stream with replay of missed messages.

    This is fully stateless - uses Redis Stream for replay and pub/sub for live updates.

    Args:
        session_id: Session ID to subscribe to
        user_id: User ID for ownership validation
        last_message_id: Last Redis Stream message ID received ("0-0" for full replay)

    Returns:
        An asyncio Queue that will receive stream chunks, or None if session not found
        or user doesn't have access
    """
    start_time = time.perf_counter()

    # Build log metadata
    log_meta = {"component": "StreamRegistry", "session_id": session_id}
    if user_id:
        log_meta["user_id"] = user_id

    logger.info(
        f"[TIMING] subscribe_to_session STARTED, session={session_id}, user={user_id}, last_msg={last_message_id}",
        extra={"json_fields": {**log_meta, "last_message_id": last_message_id}},
    )

    redis_start = time.perf_counter()
    redis = await get_redis_async()
    meta_key = _get_session_meta_key(session_id)
    meta: dict[Any, Any] = await redis.hgetall(meta_key)  # type: ignore[misc]
    hgetall_time = (time.perf_counter() - redis_start) * 1000
    logger.info(
        f"[TIMING] Redis hgetall took {hgetall_time:.1f}ms",
        extra={"json_fields": {**log_meta, "duration_ms": hgetall_time}},
    )

    # RACE CONDITION FIX: If session not found, retry with backoff.
    # Duplicate requests skip create_session and subscribe immediately; the
    # original request's create_session (a Redis hset) may not have completed
    # yet. 3 × 100ms gives a 300ms window which covers DB-write latency on the
    # original request before the hset even starts.
    if not meta:
        _max_retries = 3
        _retry_delay = 0.1  # 100ms per attempt
        for attempt in range(_max_retries):
            logger.warning(
                f"[TIMING] Session not found (attempt {attempt + 1}/{_max_retries}), "
                f"retrying after {int(_retry_delay * 1000)}ms",
                extra={"json_fields": {**log_meta, "attempt": attempt + 1}},
            )
            await asyncio.sleep(_retry_delay)
            meta = await redis.hgetall(meta_key)  # type: ignore[misc]
            if meta:
                logger.info(
                    f"[TIMING] Session found after {attempt + 1} retries",
                    extra={"json_fields": {**log_meta, "attempts": attempt + 1}},
                )
                break
        else:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"[TIMING] Session still not found in Redis after {_max_retries} retries "
                f"({elapsed:.1f}ms total)",
                extra={
                    "json_fields": {
                        **log_meta,
                        "elapsed_ms": elapsed,
                        "reason": "session_not_found_after_retry",
                    }
                },
            )
            return None

    # Note: Redis client uses decode_responses=True, so keys are strings
    session_status = meta.get("status", "")
    session_user_id = meta.get("user_id", "") or None
    log_meta["session_id"] = meta.get("session_id", "")

    # Validate ownership - if session has an owner, requester must match
    if session_user_id:
        if user_id != session_user_id:
            logger.warning(
                f"[TIMING] Access denied: user {user_id} tried to access session owned by {session_user_id}",
                extra={
                    "json_fields": {
                        **log_meta,
                        "session_owner": session_user_id,
                        "reason": "access_denied",
                    }
                },
            )
            return None

    session = _parse_session_meta(meta, session_id)
    subscriber_queue: asyncio.Queue[StreamBaseResponse] = asyncio.Queue()
    stream_key = _get_turn_stream_key(session.turn_id)

    # Replay batch capped by ``stream_replay_count``.
    xread_start = time.perf_counter()
    messages = await redis.xread(
        {stream_key: last_message_id}, block=None, count=config.stream_replay_count
    )
    xread_time = (time.perf_counter() - xread_start) * 1000
    logger.info(
        f"[TIMING] Redis xread (replay) took {xread_time:.1f}ms, status={session_status}",
        extra={
            "json_fields": {
                **log_meta,
                "duration_ms": xread_time,
                "session_status": session_status,
            }
        },
    )

    replayed_count = 0
    replay_last_id = last_message_id
    if messages:
        for _stream_name, stream_messages in messages:
            for msg_id, msg_data in stream_messages:
                replay_last_id = msg_id if isinstance(msg_id, str) else msg_id.decode()
                # Note: Redis client uses decode_responses=True, so keys are strings
                if "data" in msg_data:
                    try:
                        chunk_data = orjson.loads(msg_data["data"])
                        chunk = _reconstruct_chunk(chunk_data)
                        if chunk:
                            await subscriber_queue.put(chunk)
                            replayed_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to replay message: {e}")

    logger.info(
        f"[TIMING] Replayed {replayed_count} messages, last_id={replay_last_id}",
        extra={
            "json_fields": {
                **log_meta,
                "n_messages_replayed": replayed_count,
                "replay_last_id": replay_last_id,
            }
        },
    )

    # Step 2: If session is still running, start stream listener for live updates
    if session_status == "running":
        logger.info(
            "[TIMING] Session still running, starting _stream_listener",
            extra={"json_fields": {**log_meta, "session_status": session_status}},
        )
        listener_task = asyncio.create_task(
            _stream_listener(
                session_id, subscriber_queue, replay_last_id, log_meta, session.turn_id
            )
        )
        # Track listener task for cleanup on unsubscribe
        _listener_sessions[id(subscriber_queue)] = (session_id, listener_task)
    else:
        # Session is completed/failed - add finish marker
        logger.info(
            f"[TIMING] Session already {session_status}, adding StreamFinish",
            extra={"json_fields": {**log_meta, "session_status": session_status}},
        )
        await subscriber_queue.put(StreamFinish())

    total_time = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"[TIMING] subscribe_to_session COMPLETED in {total_time:.1f}ms; session={session_id}, "
        f"n_messages_replayed={replayed_count}",
        extra={
            "json_fields": {
                **log_meta,
                "total_time_ms": total_time,
                "n_messages_replayed": replayed_count,
            }
        },
    )
    return subscriber_queue