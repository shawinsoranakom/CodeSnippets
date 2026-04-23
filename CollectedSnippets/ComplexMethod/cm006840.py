async def session_task():
            """Background task that keeps the session alive."""
            streamable_error = None

            # Skip Streamable HTTP if we know SSE works for this server
            if preferred_transport != "sse":
                # Try Streamable HTTP first with a quick timeout
                try:
                    await logger.adebug(f"Attempting Streamable HTTP connection for session {session_id}")
                    # Use a shorter timeout for the initial connection attempt (2 seconds)
                    async with streamablehttp_client(
                        url=connection_params["url"],
                        headers=connection_params["headers"],
                        timeout=connection_params["timeout_seconds"],
                        httpx_client_factory=custom_httpx_factory,
                    ) as (read, write, _):
                        session = ClientSession(read, write)
                        async with session:
                            # Initialize with a timeout to fail fast
                            await asyncio.wait_for(session.initialize(), timeout=2.0)
                            used_transport.append("streamable_http")
                            await logger.ainfo(f"Session {session_id} connected via Streamable HTTP")
                            # Signal that session is ready
                            session_future.set_result(session)

                            # Keep the session alive until cancelled
                            import anyio

                            event = anyio.Event()
                            try:
                                await event.wait()
                            except asyncio.CancelledError:
                                await logger.ainfo(f"Session {session_id} (Streamable HTTP) is shutting down")
                except (asyncio.TimeoutError, Exception) as e:  # noqa: BLE001
                    # If Streamable HTTP fails or times out, try SSE as fallback immediately
                    streamable_error = e
                    error_type = "timed out" if isinstance(e, asyncio.TimeoutError) else "failed"
                    await logger.awarning(
                        f"Streamable HTTP {error_type} for session {session_id}: {e}. Falling back to SSE..."
                    )
            else:
                await logger.adebug(f"Skipping Streamable HTTP for session {session_id}, using cached SSE preference")

            # Try SSE if Streamable HTTP failed or if SSE is preferred
            if streamable_error is not None or preferred_transport == "sse":
                try:
                    await logger.adebug(f"Attempting SSE connection for session {session_id}")
                    # Extract SSE read timeout from connection params, default to 30s if not present
                    sse_read_timeout = connection_params.get("sse_read_timeout_seconds", 30)

                    async with sse_client(
                        connection_params["url"],
                        connection_params["headers"],
                        connection_params["timeout_seconds"],
                        sse_read_timeout,
                        httpx_client_factory=custom_httpx_factory,
                    ) as (read, write):
                        session = ClientSession(read, write)
                        async with session:
                            await session.initialize()
                            used_transport.append("sse")
                            fallback_msg = " (fallback)" if streamable_error else " (preferred)"
                            await logger.ainfo(f"Session {session_id} connected via SSE{fallback_msg}")
                            # Signal that session is ready
                            if not session_future.done():
                                session_future.set_result(session)

                            # Keep the session alive until cancelled
                            import anyio

                            event = anyio.Event()
                            try:
                                await event.wait()
                            except asyncio.CancelledError:
                                await logger.ainfo(f"Session {session_id} (SSE) is shutting down")
                except Exception as sse_error:  # noqa: BLE001
                    # Both transports failed (or just SSE if it was preferred)
                    if streamable_error:
                        await logger.aerror(
                            f"Both Streamable HTTP and SSE failed for session {session_id}. "
                            f"Streamable HTTP error: {streamable_error}. SSE error: {sse_error}"
                        )
                        if not session_future.done():
                            session_future.set_exception(
                                ValueError(
                                    f"Failed to connect via Streamable HTTP ({streamable_error}) or SSE ({sse_error})"
                                )
                            )
                    else:
                        await logger.aerror(f"SSE connection failed for session {session_id}: {sse_error}")
                        if not session_future.done():
                            session_future.set_exception(ValueError(f"Failed to connect via SSE: {sse_error}"))