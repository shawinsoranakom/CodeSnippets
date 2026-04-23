async def test_websocket_compression(self):
        with _patch_local_sources_watcher(), self._patch_app_session():
            config._set_option("server.enableWebsocketCompression", True, "test")
            await self.server.start()

            # Connect to the server, and explicitly request compression.
            ws_client = await tornado.websocket.websocket_connect(
                self.get_ws_url("/stream"), compression_options={}
            )

            # Ensure that the "permessage-deflate" extension is returned
            # from the server.
            extensions = ws_client.headers.get("Sec-Websocket-Extensions")
            self.assertIn("permessage-deflate", extensions)