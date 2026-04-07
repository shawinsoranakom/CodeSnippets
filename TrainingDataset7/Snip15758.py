def setUp(self):
        super().setUp()
        self.write_settings(
            "settings.py", apps=["django.contrib.auth", "django.contrib.contenttypes"]
        )
        self.write_settings("alternate_settings.py")