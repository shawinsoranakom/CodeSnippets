def test_default_template_loaders(self):
        """The cached template loader is always enabled by default."""
        for debug in (True, False):
            with self.subTest(DEBUG=debug), self.settings(DEBUG=debug):
                engine = DjangoTemplates(
                    {"DIRS": [], "APP_DIRS": True, "NAME": "django", "OPTIONS": {}}
                )
                self.assertEqual(
                    engine.engine.loaders,
                    [
                        (
                            "django.template.loaders.cached.Loader",
                            [
                                "django.template.loaders.filesystem.Loader",
                                "django.template.loaders.app_directories.Loader",
                            ],
                        )
                    ],
                )