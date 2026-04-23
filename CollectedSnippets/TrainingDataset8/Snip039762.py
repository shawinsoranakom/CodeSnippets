async def test_close_invalid_session(self):
        """Closing a session that doesn't exist is a no-op: no error raised."""
        await self.runtime.start()

        # Close a session that never existed
        self.runtime.close_session("no_such_session")

        # Close a valid session twice
        session_id = self.runtime.create_session(
            client=MockSessionClient(), user_info=MagicMock()
        )
        self.runtime.close_session(session_id)
        self.runtime.close_session(session_id)