async def _execute_async(
        self,
        entry: CoPilotExecutionEntry,
        cancel: threading.Event,
        cluster_lock: ClusterLock,
        log: CoPilotLogMetadata,
    ):
        """Async execution logic for a CoPilot turn.

        Calls the chat completion service (SDK or baseline) and publishes
        results to the stream registry.

        Args:
            entry: The turn payload
            cancel: Threading event to signal cancellation
            cluster_lock: Distributed lock for refresh
            log: Structured logger
        """
        last_refresh = time.monotonic()
        refresh_interval = 30.0  # Refresh lock every 30 seconds
        error_msg = None

        try:
            # Choose service based on LaunchDarkly flag.
            # Claude Code subscription forces SDK mode (CLI subprocess auth).
            config = ChatConfig()

            if config.test_mode:
                stream_fn = stream_chat_completion_dummy
                log.warning("Using DUMMY service (CHAT_TEST_MODE=true)")
                effective_mode = None
            else:
                # Enforce server-side feature-flag gate so unauthorised
                # users cannot force a mode by crafting the request.
                effective_mode = await resolve_effective_mode(entry.mode, entry.user_id)
                use_sdk = await resolve_use_sdk_for_mode(
                    effective_mode,
                    entry.user_id,
                    use_claude_code_subscription=config.use_claude_code_subscription,
                    config_default=config.use_claude_agent_sdk,
                )
                stream_fn = (
                    sdk_service.stream_chat_completion_sdk
                    if use_sdk
                    else stream_chat_completion_baseline
                )
                log.info(
                    f"Using {'SDK' if use_sdk else 'baseline'} service "
                    f"(mode={effective_mode or 'default'})"
                )

            # Stream chat completion and publish chunks to Redis.
            # stream_and_publish wraps the raw stream with registry
            # publishing so subscribers on the session Redis stream
            # (e.g. wait_for_session_result, SSE clients) receive the
            # same events as they are produced.
            raw_stream = stream_fn(
                session_id=entry.session_id,
                message=entry.message if entry.message else None,
                is_user_message=entry.is_user_message,
                user_id=entry.user_id,
                context=entry.context,
                file_ids=entry.file_ids,
                mode=effective_mode,
                model=entry.model,
                permissions=entry.permissions,
                request_arrival_at=entry.request_arrival_at,
            )
            published_stream = stream_registry.stream_and_publish(
                session_id=entry.session_id,
                turn_id=entry.turn_id,
                stream=raw_stream,
            )
            # Explicit aclose() on early exit: ``async for … break`` does
            # not close the generator, so GeneratorExit would never reach
            # stream_chat_completion_sdk, leaving its stream lock held
            # until GC eventually runs.
            try:
                async for chunk in published_stream:
                    if cancel.is_set():
                        log.info("Cancel requested, breaking stream")
                        break

                    # Capture StreamError so mark_session_completed receives
                    # the error message (stream_and_publish yields but does
                    # not publish StreamError — that's done by mark_session_completed).
                    if isinstance(chunk, StreamError):
                        error_msg = chunk.errorText
                        break

                    current_time = time.monotonic()
                    if current_time - last_refresh >= refresh_interval:
                        cluster_lock.refresh()
                        last_refresh = current_time
            finally:
                await published_stream.aclose()

            # Stream loop completed
            if cancel.is_set():
                log.info("Stream cancelled by user")

        except BaseException as e:
            # Handle all exceptions (including CancelledError) with appropriate logging
            if isinstance(e, asyncio.CancelledError):
                log.info("Turn cancelled")
                error_msg = "Operation cancelled"
            else:
                error_msg = str(e) or type(e).__name__
                log.error(f"Turn failed: {error_msg}")
            raise
        finally:
            # If no exception but user cancelled, still mark as cancelled
            if not error_msg and cancel.is_set():
                error_msg = "Operation cancelled"
            try:
                await stream_registry.mark_session_completed(
                    entry.session_id, error_message=error_msg
                )
            except Exception as mark_err:
                log.error(f"Failed to mark session completed: {mark_err}")