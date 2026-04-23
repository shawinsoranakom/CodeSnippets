async def test_start_stop(self):
        """starting and stopping the Runtime should work as expected."""
        self.assertEqual(RuntimeState.INITIAL, self.runtime.state)

        await self.runtime.start()
        self.assertEqual(RuntimeState.NO_SESSIONS_CONNECTED, self.runtime.state)

        self.runtime.stop()
        await asyncio.sleep(0)  # Wait 1 tick for the stop to be acknowledged
        self.assertEqual(RuntimeState.STOPPING, self.runtime.state)

        await self.runtime.stopped
        self.assertEqual(RuntimeState.STOPPED, self.runtime.state)