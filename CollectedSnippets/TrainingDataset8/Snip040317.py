async def test_multiple_connections(self):
        """Test multiple websockets can connect simultaneously."""
        with _patch_local_sources_watcher(), self._patch_app_session():
            await self.server.start()

            self.assertFalse(self.server.browser_is_connected)

            # Open a websocket connection
            ws_client1 = await self.ws_connect()
            self.assertTrue(self.server.browser_is_connected)

            # Open another
            ws_client2 = await self.ws_connect()
            self.assertTrue(self.server.browser_is_connected)

            # Assert that our session_infos are sane
            session_infos = list(self.server._runtime._session_info_by_id.values())
            self.assertEqual(2, len(session_infos))
            self.assertNotEqual(
                session_infos[0].session.id,
                session_infos[1].session.id,
            )

            # Close the first
            ws_client1.close()
            await asyncio.sleep(0.1)
            self.assertTrue(self.server.browser_is_connected)

            # Close the second
            ws_client2.close()
            await asyncio.sleep(0.1)
            self.assertFalse(self.server.browser_is_connected)