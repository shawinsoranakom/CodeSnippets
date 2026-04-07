def setUp(self):
        super().setUp()
        # Shorten the timeout to speed up tests.
        self.reloader.client_timeout = int(os.environ.get("DJANGO_WATCHMAN_TIMEOUT", 2))