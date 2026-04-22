async def test_handle_backmsg_exception_invalid_session(self):
        """A BackMsg exception for an invalid session should get dropped without an
        error."""
        await self.runtime.start()
        self.runtime.handle_backmsg_deserialization_exception(
            "not_a_session_id", MagicMock()
        )