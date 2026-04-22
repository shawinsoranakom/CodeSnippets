async def test_forwardmsg_hashing(self):
        """Test that outgoing ForwardMsgs contain hashes."""
        await self.runtime.start()

        client = MockSessionClient()
        session_id = self.runtime.create_session(client=client, user_info=MagicMock())

        # Create a message and ensure its hash is unset; we're testing
        # that _send_message adds the hash before it goes out.
        msg = create_dataframe_msg([1, 2, 3])
        msg.ClearField("hash")
        self.enqueue_forward_msg(session_id, msg)
        await self.tick_runtime_loop()

        received = client.forward_msgs.pop()
        self.assertEqual(populate_hash_if_needed(msg), received.hash)