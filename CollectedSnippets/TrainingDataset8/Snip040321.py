def setUp(self) -> None:
        self.original_port = config.get_option("server.port")
        return super().setUp()