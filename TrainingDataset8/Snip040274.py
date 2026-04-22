def tearDown(self) -> None:
        ComponentRegistry._instance = None
        super().tearDown()