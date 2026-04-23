async def test_handle_backmsg_invalid_session(self):
        """A BackMsg for an invalid session should get dropped without an error."""
        await self.runtime.start()
        self.runtime.handle_backmsg("not_a_session_id", MagicMock())