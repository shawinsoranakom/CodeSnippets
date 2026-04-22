async def test_forwardmsg_cacheable_flag(self):
        """Test that the metadata.cacheable flag is set properly on outgoing
        ForwardMsgs."""
        await self.runtime.start()

        client = MockSessionClient()
        session_id = self.runtime.create_session(client=client, user_info=MagicMock())

        with patch_config_options({"global.minCachedMessageSize": 0}):
            cacheable_msg = create_dataframe_msg([1, 2, 3])
            self.enqueue_forward_msg(session_id, cacheable_msg)
            await self.tick_runtime_loop()

            received = client.forward_msgs.pop()
            self.assertTrue(cacheable_msg.metadata.cacheable)
            self.assertTrue(received.metadata.cacheable)

        with patch_config_options({"global.minCachedMessageSize": 1000}):
            cacheable_msg = create_dataframe_msg([4, 5, 6])
            self.enqueue_forward_msg(session_id, cacheable_msg)
            await self.tick_runtime_loop()

            received = client.forward_msgs.pop()
            self.assertFalse(cacheable_msg.metadata.cacheable)
            self.assertFalse(received.metadata.cacheable)