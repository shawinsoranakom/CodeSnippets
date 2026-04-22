def tearDown(self):
        config.set_option(
            "server.enableWebsocketCompression", self.original_ws_compression
        )
        return super().tearDown()