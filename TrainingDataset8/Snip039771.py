async def test_handle_session_client_disconnected(self):
        """Runtime should gracefully handle `SessionClient.write_forward_msg`
        raising a `SessionClientDisconnectedError`.
        """
        await self.runtime.start()

        client = MagicMock(spec=SessionClient)
        session_id = self.runtime.create_session(client, MagicMock())

        # Send the client a message. All should be well.
        self.enqueue_forward_msg(session_id, create_dataframe_msg([1, 2, 3]))
        await self.tick_runtime_loop()

        client.write_forward_msg.assert_called_once()
        self.assertTrue(self.runtime.is_active_session(session_id))

        # Send another message - but this time the client will raise an error.
        raise_disconnected_error = MagicMock(side_effect=SessionClientDisconnectedError)
        client.write_forward_msg = raise_disconnected_error
        self.enqueue_forward_msg(session_id, create_dataframe_msg([1, 2, 3]))
        await self.tick_runtime_loop()

        # Assert that our error was raised, and that our session was disconnected.
        raise_disconnected_error.assert_called_once()
        self.assertFalse(self.runtime.is_active_session(session_id))