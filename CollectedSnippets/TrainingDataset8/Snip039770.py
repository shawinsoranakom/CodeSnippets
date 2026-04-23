async def test_handle_backmsg_after_stop(self):
        """After Runtime.stop is called, `handle_backmsg` is an error."""
        await self.runtime.start()
        self.runtime.stop()
        await self.tick_runtime_loop()

        with self.assertRaises(RuntimeStoppedError):
            self.runtime.handle_backmsg("not_a_session_id", MagicMock())