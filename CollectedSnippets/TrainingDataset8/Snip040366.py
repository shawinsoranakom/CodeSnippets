async def test_get_websocket_headers(self):
        """`get_websocket_headers()` returns the current session's
        `BrowserWebSocketHandler.request.headers`.
        """
        with self._patch_app_session():
            await self.server.start()
            await self.ws_connect()

            # Get our client's session_id and some other stuff
            self.assertEqual(1, len(self.server._runtime._session_info_by_id))
            session_id = list(self.server._runtime._session_info_by_id.keys())[0]
            session_info = self.server._runtime._session_info_by_id[session_id]
            self.assertIsInstance(session_info.client, BrowserWebSocketHandler)

            # Mock get_script_run_ctx() to return our session_id
            mock_script_run_ctx = MagicMock(spec=ScriptRunContext)
            mock_script_run_ctx.session_id = session_id
            with mock.patch(
                "streamlit.web.server.websocket_headers.get_script_run_ctx",
                return_value=mock_script_run_ctx,
            ):
                # Assert that our headers are equal to our BrowserWebSocketHandler's
                # request headers.
                headers = websocket_headers._get_websocket_headers()
                self.assertEqual(headers, dict(session_info.client.request.headers))

                # Assert the presence of some (arbitrary) headers that should always
                # be in a WebSocket request.
                self.assertIn("Host", headers)
                self.assertIn("Upgrade", headers)
                self.assertIn("Connection", headers)