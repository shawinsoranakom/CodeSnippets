async def _cleanup_session_by_id(self, server_key: str, session_id: str):
        """Clean up a specific session by server key and session ID."""
        if server_key not in self.sessions_by_server:
            return

        server_data = self.sessions_by_server[server_key]
        # Handle both old and new session structure
        if isinstance(server_data, dict) and "sessions" in server_data:
            sessions = server_data["sessions"]
        else:
            # Handle old structure where sessions were stored directly
            sessions = server_data

        if session_id not in sessions:
            return

        session_info = sessions[session_id]
        try:
            # First try to properly close the session if it exists
            if "session" in session_info:
                session = session_info["session"]

                # Try async close first (aclose method)
                if hasattr(session, "aclose"):
                    try:
                        await session.aclose()
                        await logger.adebug("Successfully closed session %s using aclose()", session_id)
                    except Exception as e:  # noqa: BLE001
                        await logger.adebug("Error closing session %s with aclose(): %s", session_id, e)

                # If no aclose, try regular close method
                elif hasattr(session, "close"):
                    try:
                        # Check if close() is awaitable using inspection
                        if inspect.iscoroutinefunction(session.close):
                            # It's an async method
                            await session.close()
                            await logger.adebug("Successfully closed session %s using async close()", session_id)
                        else:
                            # Try calling it and check if result is awaitable
                            close_result = session.close()
                            if inspect.isawaitable(close_result):
                                await close_result
                                await logger.adebug(
                                    "Successfully closed session %s using awaitable close()", session_id
                                )
                            else:
                                # It's a synchronous close
                                await logger.adebug("Successfully closed session %s using sync close()", session_id)
                    except Exception as e:  # noqa: BLE001
                        await logger.adebug("Error closing session %s with close(): %s", session_id, e)

            # Cancel the background task which will properly close the session
            if "task" in session_info:
                task = session_info["task"]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        await logger.ainfo(f"Cancelled task for session {session_id}")
        except Exception as e:  # noqa: BLE001
            await logger.awarning(f"Error cleaning up session {session_id}: {e}")
        finally:
            # Remove from sessions dict
            del sessions[session_id]