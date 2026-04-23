def setUp(self) -> None:
        self.original_address = config.get_option("server.address")
        return super().setUp()