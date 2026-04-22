def tearDown(self) -> None:
        super().tearDown()
        # Server._create_app() will create the Runtime singleton.
        # We null it out in tearDown() so that it doesn't interfere with
        # future tests.
        Runtime._instance = None