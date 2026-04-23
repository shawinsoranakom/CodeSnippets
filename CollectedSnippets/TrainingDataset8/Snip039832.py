def tearDown(self) -> None:
        super().tearDown()
        Runtime._instance = None