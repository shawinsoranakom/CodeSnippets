async def test_start_stop(self):
        """Test that we can start and stop the server."""
        with _patch_local_sources_watcher(), self._patch_app_session():
            await self.server.start()
            self.assertEqual(
                RuntimeState.NO_SESSIONS_CONNECTED, self.server._runtime._state
            )

            await self.ws_connect()
            self.assertEqual(
                RuntimeState.ONE_OR_MORE_SESSIONS_CONNECTED, self.server._runtime._state
            )

            self.server.stop()
            await asyncio.sleep(0)  # Wait a tick for the stop to be acknowledged
            self.assertEqual(RuntimeState.STOPPING, self.server._runtime._state)

            await asyncio.sleep(0.1)
            self.assertEqual(RuntimeState.STOPPED, self.server._runtime._state)