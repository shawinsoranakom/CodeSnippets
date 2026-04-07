def test_cache_path_not_conflict(self):
        root = pathlib.Path.cwd()
        for setting in ("MEDIA_ROOT", "STATIC_ROOT", "STATICFILES_DIRS"):
            settings = self.get_settings(setting, root / "cache", root / "other")
            with self.subTest(setting=setting), self.settings(**settings):
                self.assertEqual(check_cache_location_not_exposed(None), [])