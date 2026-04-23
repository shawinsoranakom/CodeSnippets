async def test_websocket_connect(self):
        """Test that we can connect to the server via websocket."""
        with _patch_local_sources_watcher(), self._patch_app_session():
            await self.server.start()

            self.assertFalse(self.server.browser_is_connected)

            # Open a websocket connection
            ws_client = await self.ws_connect()
            self.assertTrue(self.server.browser_is_connected)

            # Get this client's SessionInfo object
            self.assertEqual(1, len(self.server._runtime._session_info_by_id))
            session_info = list(self.server._runtime._session_info_by_id.values())[0]

            # Close the connection
            ws_client.close()
            await asyncio.sleep(0.1)
            self.assertFalse(self.server.browser_is_connected)

            # Ensure AppSession.shutdown() was called, and that our
            # SessionInfo was cleared.
            session_info.session.shutdown.assert_called_once()
            self.assertEqual(0, len(self.server._runtime._session_info_by_id))