def tearDown(self) -> None:
        config.set_option("server.port", self.original_port)
        return super().tearDown()