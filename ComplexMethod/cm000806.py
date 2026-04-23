async def _stream_listener(
    session_id: str,
    subscriber_queue: asyncio.Queue[StreamBaseResponse],
    last_replayed_id: str,
    log_meta: dict | None = None,
    turn_id: str = "",
) -> None:
    """Listen to Redis Stream for new messages using blocking XREAD.

    This approach avoids the duplicate message issue that can occur with pub/sub
    when messages are published during the gap between replay and subscription.

    Args:
        session_id: Session ID to listen for
        subscriber_queue: Queue to deliver messages to
        last_replayed_id: Last message ID from replay (continue from here)
        log_meta: Structured logging metadata
        turn_id: Per-turn UUID for stream key resolution
    """
    start_time = time.perf_counter()

    # Use provided log_meta or build minimal one
    if log_meta is None:
        log_meta = {"component": "StreamRegistry", "session_id": session_id}

    logger.info(
        f"[TIMING] _stream_listener STARTED, session={session_id}, last_id={last_replayed_id}",
        extra={"json_fields": {**log_meta, "last_replayed_id": last_replayed_id}},
    )

    queue_id = id(subscriber_queue)
    # Track the last successfully delivered message ID for recovery hints
    last_delivered_id = last_replayed_id
    messages_delivered = 0
    first_message_time = None
    xread_count = 0

    try:
        redis = await get_redis_async()
        stream_key = _get_turn_stream_key(turn_id)
        current_id = last_replayed_id

        while True:
            # Block for up to 5 seconds waiting for new messages
            # This allows periodic checking if session is still running
            # Short timeout prevents frontend timeout (12s) while waiting for heartbeats (15s)
            xread_start = time.perf_counter()
            xread_count += 1
            messages = await redis.xread(
                {stream_key: current_id}, block=5000, count=100
            )
            xread_time = (time.perf_counter() - xread_start) * 1000

            if messages:
                msg_count = sum(len(msgs) for _, msgs in messages)
                logger.info(
                    f"[TIMING] xread #{xread_count} returned {msg_count} messages in {xread_time:.1f}ms",
                    extra={
                        "json_fields": {
                            **log_meta,
                            "xread_count": xread_count,
                            "n_messages": msg_count,
                            "duration_ms": xread_time,
                        }
                    },
                )
            elif xread_time > 1000:
                # Only log timeouts (30s blocking)
                logger.info(
                    f"[TIMING] xread #{xread_count} timeout after {xread_time:.1f}ms",
                    extra={
                        "json_fields": {
                            **log_meta,
                            "xread_count": xread_count,
                            "duration_ms": xread_time,
                            "reason": "timeout",
                        }
                    },
                )

            if not messages:
                # Timeout - check if session is still running
                meta_key = _get_session_meta_key(session_id)
                status = await redis.hget(meta_key, "status")  # type: ignore[misc]
                # Stop if session metadata is gone (TTL expired) or status is not "running"
                if status != "running":
                    try:
                        await asyncio.wait_for(
                            subscriber_queue.put(StreamFinish()),
                            timeout=QUEUE_PUT_TIMEOUT,
                        )
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Timeout delivering finish event for session {session_id}"
                        )
                    break
                # Session still running - send heartbeat to keep connection alive
                # This prevents frontend timeout (12s) during long-running operations
                try:
                    await asyncio.wait_for(
                        subscriber_queue.put(StreamHeartbeat()),
                        timeout=QUEUE_PUT_TIMEOUT,
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        f"Timeout delivering heartbeat for session {session_id}"
                    )
                continue

            for _stream_name, stream_messages in messages:
                for msg_id, msg_data in stream_messages:
                    current_id = msg_id if isinstance(msg_id, str) else msg_id.decode()

                    if "data" not in msg_data:
                        continue

                    try:
                        chunk_data = orjson.loads(msg_data["data"])
                        chunk = _reconstruct_chunk(chunk_data)
                        if chunk:
                            try:
                                await asyncio.wait_for(
                                    subscriber_queue.put(chunk),
                                    timeout=QUEUE_PUT_TIMEOUT,
                                )
                                # Update last delivered ID on successful delivery
                                last_delivered_id = current_id
                                messages_delivered += 1
                                if first_message_time is None:
                                    first_message_time = time.perf_counter()
                                    elapsed = (first_message_time - start_time) * 1000
                                    logger.info(
                                        f"[TIMING] FIRST live message at {elapsed:.1f}ms, type={type(chunk).__name__}",
                                        extra={
                                            "json_fields": {
                                                **log_meta,
                                                "elapsed_ms": elapsed,
                                                "chunk_type": type(chunk).__name__,
                                            }
                                        },
                                    )
                            except asyncio.TimeoutError:
                                logger.warning(
                                    f"[TIMING] Subscriber queue full, delivery timed out after {QUEUE_PUT_TIMEOUT}s",
                                    extra={
                                        "json_fields": {
                                            **log_meta,
                                            "timeout_s": QUEUE_PUT_TIMEOUT,
                                            "reason": "queue_full",
                                        }
                                    },
                                )
                                # Send overflow error with recovery info
                                try:
                                    overflow_error = StreamError(
                                        errorText="Message delivery timeout - some messages may have been missed",
                                        code="QUEUE_OVERFLOW",
                                        details={
                                            "last_delivered_id": last_delivered_id,
                                            "recovery_hint": f"Reconnect with last_message_id={last_delivered_id}",
                                        },
                                    )
                                    subscriber_queue.put_nowait(overflow_error)
                                except asyncio.QueueFull:
                                    # Queue is completely stuck, nothing more we can do
                                    logger.error(
                                        f"Cannot deliver overflow error for session {session_id}, "
                                        "queue completely blocked"
                                    )

                            # Stop listening on finish
                            if isinstance(chunk, StreamFinish):
                                total_time = (time.perf_counter() - start_time) * 1000
                                logger.info(
                                    f"[TIMING] StreamFinish received in {total_time / 1000:.1f}s; delivered={messages_delivered}",
                                    extra={
                                        "json_fields": {
                                            **log_meta,
                                            "total_time_ms": total_time,
                                            "messages_delivered": messages_delivered,
                                        }
                                    },
                                )
                                return
                    except Exception as e:
                        logger.warning(
                            f"Error processing stream message: {e}",
                            extra={"json_fields": {**log_meta, "error": str(e)}},
                        )

    except asyncio.CancelledError:
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"[TIMING] _stream_listener CANCELLED after {elapsed:.1f}ms, delivered={messages_delivered}",
            extra={
                "json_fields": {
                    **log_meta,
                    "elapsed_ms": elapsed,
                    "messages_delivered": messages_delivered,
                    "reason": "cancelled",
                }
            },
        )
        raise  # Re-raise to propagate cancellation
    except Exception as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"[TIMING] _stream_listener ERROR after {elapsed:.1f}ms: {e}",
            extra={"json_fields": {**log_meta, "elapsed_ms": elapsed, "error": str(e)}},
        )
        # On error, send finish to unblock subscriber
        try:
            await asyncio.wait_for(
                subscriber_queue.put(StreamFinish()),
                timeout=QUEUE_PUT_TIMEOUT,
            )
        except (asyncio.TimeoutError, asyncio.QueueFull):
            logger.warning(
                "Could not deliver finish event after error",
                extra={"json_fields": log_meta},
            )
    finally:
        # Clean up listener session mapping on exit
        total_time = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"[TIMING] _stream_listener FINISHED in {total_time / 1000:.1f}s; session={session_id}, "
            f"delivered={messages_delivered}, xread_count={xread_count}",
            extra={
                "json_fields": {
                    **log_meta,
                    "total_time_ms": total_time,
                    "messages_delivered": messages_delivered,
                    "xread_count": xread_count,
                }
            },
        )
        _listener_sessions.pop(queue_id, None)