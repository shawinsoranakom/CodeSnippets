async def test_create_session_after_stop(self):
        """After Runtime.stop is called, `create_session` is an error."""
        await self.runtime.start()
        self.runtime.stop()
        await self.tick_runtime_loop()

        with self.assertRaises(RuntimeStoppedError):
            self.runtime.create_session(MagicMock(), MagicMock())