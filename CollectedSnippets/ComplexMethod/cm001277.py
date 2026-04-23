async def stream_chat_post(
    session_id: str,
    request: StreamChatRequest,
    user_id: str = Security(auth.get_user_id),
):
    """Start a new turn OR queue a follow-up — decided server-side.

    - **Session idle**: starts a turn.  Returns an SSE stream (``text/event-stream``)
      with Vercel AI SDK chunks (text fragments, tool-call UI, tool results).
      The generation runs in a background task that survives client disconnects;
      reconnect via ``GET /sessions/{session_id}/stream`` to resume.

    - **Session has a turn in flight**: pushes the message into the per-session
      pending buffer and returns ``202 application/json`` with
      ``QueuePendingMessageResponse``.  The executor running the current turn
      drains the buffer between tool-call rounds (baseline) or at the start of
      the next turn (SDK).  Clients should detect the 202 and surface the
      message as a queued-chip in the UI.

    Args:
        session_id: The chat session identifier.
        request: Request body with message, is_user_message, and optional context.
        user_id: Authenticated user ID.
    """
    import asyncio
    import time

    stream_start_time = time.perf_counter()
    # Wall-clock arrival time, propagated to the executor so the turn-start
    # drain can order pending messages relative to this request (pending
    # pushed BEFORE this instant were typed earlier; pending pushed AFTER
    # are race-path follow-ups typed while /stream was still processing).
    request_arrival_at = time.time()
    log_meta = {"component": "ChatStream", "session_id": session_id, "user_id": user_id}

    logger.info(
        f"[TIMING] stream_chat_post STARTED, session={session_id}, "
        f"user={user_id}, message_len={len(request.message)}",
        extra={"json_fields": log_meta},
    )
    session = await _validate_and_get_session(session_id, user_id)
    builder_permissions = resolve_session_permissions(session)

    # Self-defensive queue-fallback: if a turn is already running, don't race
    # it on the cluster lock — drop the message into the pending buffer and
    # return 202 so the caller can render a chip.  Both UI chips and autopilot
    # block follow-ups route through this path; keeping the decision on the
    # server means every caller gets uniform behaviour.
    if (
        request.is_user_message
        and request.message
        and await is_turn_in_flight(session_id)
    ):
        response = await queue_pending_for_http(
            session_id=session_id,
            user_id=user_id,
            message=request.message,
            context=request.context,
            file_ids=request.file_ids,
        )
        return JSONResponse(status_code=202, content=response.model_dump())

    logger.info(
        f"[TIMING] session validated in {(time.perf_counter() - stream_start_time) * 1000:.1f}ms",
        extra={
            "json_fields": {
                **log_meta,
                "duration_ms": (time.perf_counter() - stream_start_time) * 1000,
            }
        },
    )

    # Pre-turn rate limit check (cost-based, microdollars).
    # check_rate_limit short-circuits internally when both limits are 0.
    # Global defaults sourced from LaunchDarkly, falling back to config.
    if user_id:
        try:
            daily_limit, weekly_limit, _ = await get_global_rate_limits(
                user_id,
                config.daily_cost_limit_microdollars,
                config.weekly_cost_limit_microdollars,
            )
            await check_rate_limit(
                user_id=user_id,
                daily_cost_limit=daily_limit,
                weekly_cost_limit=weekly_limit,
            )
        except RateLimitExceeded as e:
            raise HTTPException(status_code=429, detail=str(e)) from e

    # Enrich message with file metadata if file_ids are provided.
    # Also sanitise file_ids so only validated, workspace-scoped IDs are
    # forwarded downstream (e.g. to the executor via enqueue_copilot_turn).
    sanitized_file_ids: list[str] | None = None
    if request.file_ids:
        files = await resolve_workspace_files(user_id, request.file_ids)
        sanitized_file_ids = [wf.id for wf in files] or None
        request.message += build_files_block(files)

    # Atomically append user message to session BEFORE creating task to avoid
    # race condition where GET_SESSION sees task as "running" but message isn't
    # saved yet.  append_and_save_message returns None when a duplicate is
    # detected — in that case skip enqueue to avoid processing the message twice.
    is_duplicate_message = False
    if request.message:
        message = ChatMessage(
            role="user" if request.is_user_message else "assistant",
            content=request.message,
        )
        logger.info(f"[STREAM] Saving user message to session {session_id}")
        is_duplicate_message = (
            await append_and_save_message(session_id, message)
        ) is None
        logger.info(f"[STREAM] User message saved for session {session_id}")
        if not is_duplicate_message and request.is_user_message:
            track_user_message(
                user_id=user_id,
                session_id=session_id,
                message_length=len(request.message),
            )

    # Create a task in the stream registry for reconnection support.
    # For duplicate messages, skip create_session entirely so the infra-retry
    # client subscribes to the *existing* turn's Redis stream and receives the
    # in-progress executor output rather than an empty stream.
    turn_id = ""
    if not is_duplicate_message:
        turn_id = str(uuid4())
        log_meta["turn_id"] = turn_id
        session_create_start = time.perf_counter()
        await stream_registry.create_session(
            session_id=session_id,
            user_id=user_id,
            tool_call_id="chat_stream",
            tool_name="chat",
            turn_id=turn_id,
        )
        logger.info(
            f"[TIMING] create_session completed in {(time.perf_counter() - session_create_start) * 1000:.1f}ms",
            extra={
                "json_fields": {
                    **log_meta,
                    "duration_ms": (time.perf_counter() - session_create_start) * 1000,
                }
            },
        )
        await enqueue_copilot_turn(
            session_id=session_id,
            user_id=user_id,
            message=request.message,
            turn_id=turn_id,
            is_user_message=request.is_user_message,
            context=request.context,
            file_ids=sanitized_file_ids,
            mode=request.mode,
            model=request.model,
            permissions=builder_permissions,
            request_arrival_at=request_arrival_at,
        )
    else:
        logger.info(
            f"[STREAM] Duplicate message detected for session {session_id}, skipping enqueue"
        )

    setup_time = (time.perf_counter() - stream_start_time) * 1000
    logger.info(
        f"[TIMING] Task enqueued to RabbitMQ, setup={setup_time:.1f}ms",
        extra={"json_fields": {**log_meta, "setup_time_ms": setup_time}},
    )

    # Per-turn stream is always fresh (unique turn_id), subscribe from beginning
    subscribe_from_id = "0-0"

    # SSE endpoint that subscribes to the task's stream
    async def event_generator() -> AsyncGenerator[str, None]:
        import time as time_module

        event_gen_start = time_module.perf_counter()
        logger.info(
            f"[TIMING] event_generator STARTED, turn={turn_id}, session={session_id}, "
            f"user={user_id}",
            extra={"json_fields": log_meta},
        )
        subscriber_queue = None
        first_chunk_yielded = False
        chunks_yielded = 0
        try:
            # Subscribe from the position we captured before enqueuing
            # This avoids replaying old messages while catching all new ones
            subscriber_queue = await stream_registry.subscribe_to_session(
                session_id=session_id,
                user_id=user_id,
                last_message_id=subscribe_from_id,
            )

            if subscriber_queue is None:
                yield StreamFinish().to_sse()
                return

            # Read from the subscriber queue and yield to SSE
            logger.info(
                "[TIMING] Starting to read from subscriber_queue",
                extra={"json_fields": log_meta},
            )
            while True:
                try:
                    chunk = await asyncio.wait_for(subscriber_queue.get(), timeout=10.0)
                    chunks_yielded += 1

                    if not first_chunk_yielded:
                        first_chunk_yielded = True
                        elapsed = time_module.perf_counter() - event_gen_start
                        logger.info(
                            f"[TIMING] FIRST CHUNK from queue at {elapsed:.2f}s, "
                            f"type={type(chunk).__name__}",
                            extra={
                                "json_fields": {
                                    **log_meta,
                                    "chunk_type": type(chunk).__name__,
                                    "elapsed_ms": elapsed * 1000,
                                }
                            },
                        )

                    yield chunk.to_sse()

                    if isinstance(chunk, StreamFinish):
                        total_time = time_module.perf_counter() - event_gen_start
                        logger.info(
                            f"[TIMING] StreamFinish received in {total_time:.2f}s; "
                            f"n_chunks={chunks_yielded}",
                            extra={
                                "json_fields": {
                                    **log_meta,
                                    "chunks_yielded": chunks_yielded,
                                    "total_time_ms": total_time * 1000,
                                }
                            },
                        )
                        break

                except asyncio.TimeoutError:
                    yield StreamHeartbeat().to_sse()

        except GeneratorExit:
            logger.info(
                f"[TIMING] GeneratorExit (client disconnected), chunks={chunks_yielded}",
                extra={
                    "json_fields": {
                        **log_meta,
                        "chunks_yielded": chunks_yielded,
                        "reason": "client_disconnect",
                    }
                },
            )
        except Exception as e:
            elapsed = (time_module.perf_counter() - event_gen_start) * 1000
            logger.error(
                f"[TIMING] event_generator ERROR after {elapsed:.1f}ms: {e}",
                extra={
                    "json_fields": {**log_meta, "elapsed_ms": elapsed, "error": str(e)}
                },
            )
            # Surface error to frontend so it doesn't appear stuck
            yield StreamError(
                errorText="An error occurred. Please try again.",
                code="stream_error",
            ).to_sse()
            yield StreamFinish().to_sse()
        finally:
            # Unsubscribe when client disconnects or stream ends
            if subscriber_queue is not None:
                try:
                    await stream_registry.unsubscribe_from_session(
                        session_id, subscriber_queue
                    )
                except Exception as unsub_err:
                    logger.error(
                        f"Error unsubscribing from session {session_id}: {unsub_err}",
                        exc_info=True,
                    )
            # AI SDK protocol termination - always yield even if unsubscribe fails
            total_time = time_module.perf_counter() - event_gen_start
            logger.info(
                f"[TIMING] event_generator FINISHED in {total_time:.2f}s; "
                f"turn={turn_id}, session={session_id}, n_chunks={chunks_yielded}",
                extra={
                    "json_fields": {
                        **log_meta,
                        "total_time_ms": total_time * 1000,
                        "chunks_yielded": chunks_yielded,
                    }
                },
            )
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "x-vercel-ai-ui-message-stream": "v1",  # AI SDK protocol header
        },
    )