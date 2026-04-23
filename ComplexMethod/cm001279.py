async def event_generator() -> AsyncGenerator[str, None]:
        chunk_count = 0
        first_chunk_type: str | None = None
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(subscriber_queue.get(), timeout=10.0)
                    if chunk_count < 3:
                        logger.info(
                            "Resume stream chunk",
                            extra={
                                "session_id": session_id,
                                "chunk_type": str(chunk.type),
                            },
                        )
                    if not first_chunk_type:
                        first_chunk_type = str(chunk.type)
                    chunk_count += 1
                    yield chunk.to_sse()

                    if isinstance(chunk, StreamFinish):
                        break
                except asyncio.TimeoutError:
                    yield StreamHeartbeat().to_sse()
        except GeneratorExit:
            pass
        except Exception as e:
            logger.error(f"Error in resume stream for session {session_id}: {e}")
        finally:
            try:
                await stream_registry.unsubscribe_from_session(
                    session_id, subscriber_queue
                )
            except Exception as unsub_err:
                logger.error(
                    f"Error unsubscribing from session {active_session.session_id}: {unsub_err}",
                    exc_info=True,
                )
            logger.info(
                "Resume stream completed",
                extra={
                    "session_id": session_id,
                    "n_chunks": chunk_count,
                    "first_chunk_type": first_chunk_type,
                },
            )
            yield "data: [DONE]\n\n"