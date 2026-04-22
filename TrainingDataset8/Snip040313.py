def setUp(self) -> None:
        self.original_ws_compression = config.get_option(
            "server.enableWebsocketCompression"
        )
        return super().setUp()