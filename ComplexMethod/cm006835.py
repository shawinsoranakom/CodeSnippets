async def get_session(self, context_id: str, connection_params, transport_type: str):
        """Get or create a session with improved reuse strategy.

        The key insight is that we should reuse sessions based on the server
        identity (command + args for stdio, URL for Streamable HTTP) rather than the context_id.
        This prevents creating a new subprocess for each unique context.
        """
        server_key = self._get_server_key(connection_params, transport_type)

        # Ensure server entry exists
        if server_key not in self.sessions_by_server:
            self.sessions_by_server[server_key] = {"sessions": {}, "last_cleanup": asyncio.get_event_loop().time()}

        server_data = self.sessions_by_server[server_key]
        sessions = server_data["sessions"]

        # Try to find a healthy existing session
        for session_id, session_info in list(sessions.items()):
            session = session_info["session"]
            task = session_info["task"]

            # Check if session is still alive
            if not task.done():
                # Update last used time
                session_info["last_used"] = asyncio.get_event_loop().time()

                # Quick health check
                if await self._validate_session_connectivity(session):
                    await logger.adebug(f"Reusing existing session {session_id} for server {server_key}")
                    # record mapping & bump ref-count for backwards compatibility
                    self._context_to_session[context_id] = (server_key, session_id)
                    self._session_refcount[(server_key, session_id)] = (
                        self._session_refcount.get((server_key, session_id), 0) + 1
                    )
                    return session
                await logger.ainfo(f"Session {session_id} for server {server_key} failed health check, cleaning up")
                await self._cleanup_session_by_id(server_key, session_id)
            else:
                # Task is done, clean up
                await logger.ainfo(f"Session {session_id} for server {server_key} task is done, cleaning up")
                await self._cleanup_session_by_id(server_key, session_id)

        # Check if we've reached the maximum number of sessions for this server
        if len(sessions) >= get_max_sessions_per_server():
            # Remove the oldest session
            oldest_session_id = min(sessions.keys(), key=lambda x: sessions[x]["last_used"])
            await logger.ainfo(
                f"Maximum sessions reached for server {server_key}, removing oldest session {oldest_session_id}"
            )
            await self._cleanup_session_by_id(server_key, oldest_session_id)

        # Create new session
        session_id = f"{server_key}_{len(sessions)}"
        await logger.ainfo(f"Creating new session {session_id} for server {server_key}")

        if transport_type == "stdio":
            session, task = await self._create_stdio_session(session_id, connection_params)
            actual_transport = "stdio"
        elif transport_type == "streamable_http":
            # Pass the cached transport preference if available
            preferred_transport = self._transport_preference.get(server_key)
            session, task, actual_transport = await self._create_streamable_http_session(
                session_id, connection_params, preferred_transport
            )
            # Cache the transport that worked for future connections
            self._transport_preference[server_key] = actual_transport
        else:
            msg = f"Unknown transport type: {transport_type}"
            raise ValueError(msg)

        # Store session info with the actual transport used
        sessions[session_id] = {
            "session": session,
            "task": task,
            "type": actual_transport,
            "last_used": asyncio.get_event_loop().time(),
        }

        # register mapping & initial ref-count for the new session
        self._context_to_session[context_id] = (server_key, session_id)
        self._session_refcount[(server_key, session_id)] = 1

        return session