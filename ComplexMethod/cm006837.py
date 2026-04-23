async def cleanup_all(self):
        """Clean up all sessions."""
        # Cancel periodic cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        # Clean up all sessions
        for server_key in list(self.sessions_by_server.keys()):
            server_data = self.sessions_by_server[server_key]
            # Handle both old and new session structure
            if isinstance(server_data, dict) and "sessions" in server_data:
                sessions = server_data["sessions"]
            else:
                # Handle old structure where sessions were stored directly
                sessions = server_data

            for session_id in list(sessions.keys()):
                await self._cleanup_session_by_id(server_key, session_id)

        # Clear the sessions_by_server structure completely
        self.sessions_by_server.clear()

        # Clear compatibility maps
        self._context_to_session.clear()
        self._session_refcount.clear()

        # Clear all background tasks
        for task in list(self._background_tasks):
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        # Give a bit more time for subprocess transports to clean up
        # This helps prevent the BaseSubprocessTransport.__del__ warnings
        await asyncio.sleep(0.5)