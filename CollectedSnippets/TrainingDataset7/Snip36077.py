def setUp(self):
        super().setUp()
        # Shorten the sleep time to speed up tests.
        self.reloader.SLEEP_TIME = 0.01