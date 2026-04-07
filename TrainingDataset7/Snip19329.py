def test_staticfiles_dirs_prefix_not_conflict(self):
        root = pathlib.Path.cwd()
        settings = self.get_settings(
            "STATICFILES_DIRS",
            root / "cache",
            ("prefix", root / "other"),
        )
        with self.settings(**settings):
            self.assertEqual(check_cache_location_not_exposed(None), [])