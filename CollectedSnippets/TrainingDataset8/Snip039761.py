async def test_multiple_sessions(self):
        """Multiple sessions can be connected."""
        await self.runtime.start()

        session_ids = []
        for _ in range(3):
            session_id = self.runtime.create_session(
                client=MockSessionClient(),
                user_info=MagicMock(),
            )

            self.assertEqual(
                RuntimeState.ONE_OR_MORE_SESSIONS_CONNECTED, self.runtime.state
            )
            session_ids.append(session_id)

        for i in range(len(session_ids)):
            self.runtime.close_session(session_ids[i])
            expected_state = (
                RuntimeState.NO_SESSIONS_CONNECTED
                if i == len(session_ids) - 1
                else RuntimeState.ONE_OR_MORE_SESSIONS_CONNECTED
            )
            self.assertEqual(expected_state, self.runtime.state)

        self.assertEqual(RuntimeState.NO_SESSIONS_CONNECTED, self.runtime.state)