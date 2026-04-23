async def test_is_active_session(self):
        """`is_active_session` should work as expected."""
        await self.runtime.start()
        session_id = self.runtime.create_session(
            client=MockSessionClient(), user_info=MagicMock()
        )
        self.assertTrue(self.runtime.is_active_session(session_id))
        self.assertFalse(self.runtime.is_active_session("not_a_session_id"))

        self.runtime.close_session(session_id)
        self.assertFalse(self.runtime.is_active_session(session_id))