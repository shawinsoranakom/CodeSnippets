async def test_duplicate_forwardmsg_caching(self):
        """Test that duplicate ForwardMsgs are sent only once."""
        with patch_config_options({"global.minCachedMessageSize": 0}):
            await self.runtime.start()

            client = MockSessionClient()
            session_id = self.runtime.create_session(
                client=client, user_info=MagicMock()
            )

            msg1 = create_dataframe_msg([1, 2, 3], 1)

            # Send the message, and read it back. It will not have been cached.
            self.enqueue_forward_msg(session_id, msg1)
            await self.tick_runtime_loop()

            uncached = client.forward_msgs.pop()
            self.assertEqual("delta", uncached.WhichOneof("type"))

            # Send an equivalent message. This time, it should be cached,
            # and a "hash_reference" message should be received instead.
            msg2 = create_dataframe_msg([1, 2, 3], 123)
            self.enqueue_forward_msg(session_id, msg2)
            await self.tick_runtime_loop()

            cached = client.forward_msgs.pop()
            self.assertEqual("ref_hash", cached.WhichOneof("type"))
            # We should have the *hash* of msg1 and msg2:
            self.assertEqual(msg1.hash, cached.ref_hash)
            self.assertEqual(msg2.hash, cached.ref_hash)
            # And the same *metadata* as msg2:
            self.assertEqual(msg2.metadata, cached.metadata)