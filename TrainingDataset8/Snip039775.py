async def test_forwardmsg_cache_clearing(self):
        """Test that the ForwardMsgCache gets properly cleared when scripts
        finish running.
        """
        with patch_config_options(
            {"global.minCachedMessageSize": 0, "global.maxCachedMessageAge": 1}
        ):
            await self.runtime.start()

            client = MockSessionClient()
            session_id = self.runtime.create_session(
                client=client, user_info=MagicMock()
            )

            data_msg = create_dataframe_msg([1, 2, 3])

            async def finish_script(success: bool) -> None:
                status = (
                    ForwardMsg.FINISHED_SUCCESSFULLY
                    if success
                    else ForwardMsg.FINISHED_WITH_COMPILE_ERROR
                )
                finish_msg = create_script_finished_message(status)
                self.enqueue_forward_msg(session_id, finish_msg)
                await self.tick_runtime_loop()

            def is_data_msg_cached() -> bool:
                return (
                    self.runtime._message_cache.get_message(data_msg.hash) is not None
                )

            async def send_data_msg() -> None:
                self.enqueue_forward_msg(session_id, data_msg)
                await self.tick_runtime_loop()

            # Send a cacheable message. It should be cached.
            await send_data_msg()
            self.assertTrue(is_data_msg_cached())

            # End the script with a compile error. Nothing should change;
            # compile errors don't increase the age of items in the cache.
            await finish_script(False)
            self.assertTrue(is_data_msg_cached())

            # End the script successfully. Nothing should change, because
            # the age of the cached message is now 1.
            await finish_script(True)
            self.assertTrue(is_data_msg_cached())

            # Send the message again. This should reset its age to 0 in the
            # cache, so it won't be evicted when the script next finishes.
            await send_data_msg()
            self.assertTrue(is_data_msg_cached())

            # Finish the script. The cached message age is now 1.
            await finish_script(True)
            self.assertTrue(is_data_msg_cached())

            # Finish again. The cached message age will be 2, and so it
            # should be evicted from the cache.
            await finish_script(True)
            self.assertFalse(is_data_msg_cached())