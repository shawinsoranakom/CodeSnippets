def test_cache_path_inside_media_static_setting(self):
        root = pathlib.Path.cwd()
        for setting in ("MEDIA_ROOT", "STATIC_ROOT", "STATICFILES_DIRS"):
            settings = self.get_settings(setting, root / "cache", root)
            with self.subTest(setting=setting), self.settings(**settings):
                msg = self.warning_message % ("is inside", setting)
                self.assertEqual(
                    check_cache_location_not_exposed(None),
                    [
                        Warning(msg, id="caches.W002"),
                    ],
                )