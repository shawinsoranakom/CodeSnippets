def tearDown(self) -> None:
        config.set_option("server.address", self.original_address)
        return super().tearDown()