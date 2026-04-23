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