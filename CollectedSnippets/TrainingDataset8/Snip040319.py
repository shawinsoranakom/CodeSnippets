async def test_websocket_compression_disabled(self):
        with _patch_local_sources_watcher(), self._patch_app_session():
            config._set_option("server.enableWebsocketCompression", False, "test")
            await self.server.start()

            # Connect to the server, and explicitly request compression.
            ws_client = await tornado.websocket.websocket_connect(
                self.get_ws_url("/stream"), compression_options={}
            )

            # Ensure that the "Sec-Websocket-Extensions" header is not
            # present in the response from the server.
            self.assertIsNone(ws_client.headers.get("Sec-Websocket-Extensions"))