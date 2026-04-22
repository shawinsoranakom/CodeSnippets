async def test_create_session(self):
        """We can create and remove a single session."""
        await self.runtime.start()

        session_id = self.runtime.create_session(
            client=MockSessionClient(), user_info=MagicMock()
        )
        self.assertEqual(
            RuntimeState.ONE_OR_MORE_SESSIONS_CONNECTED, self.runtime.state
        )

        self.runtime.close_session(session_id)
        self.assertEqual(RuntimeState.NO_SESSIONS_CONNECTED, self.runtime.state)