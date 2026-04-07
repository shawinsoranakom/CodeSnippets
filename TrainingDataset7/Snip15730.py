def setUp(self):
        super().setUp()
        self.write_settings(
            "settings.py",
            ["django.contrib.auth", "django.contrib.contenttypes", "admin_scripts"],
        )