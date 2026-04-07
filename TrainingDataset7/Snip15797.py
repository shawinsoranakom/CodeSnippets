def setUp(self):
        super().setUp()
        self.write_settings(
            "settings.py",
            sdict={
                "ALLOWED_HOSTS": [],
                "DEBUG": False,
            },
        )