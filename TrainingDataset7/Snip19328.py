def test_staticfiles_dirs_prefix(self):
        root = pathlib.Path.cwd()
        tests = [
            (root, root, "matches"),
            (root / "cache", root, "is inside"),
            (root, root / "other", "contains"),
        ]
        for cache_path, setting_path, msg in tests:
            settings = self.get_settings(
                "STATICFILES_DIRS",
                cache_path,
                ("prefix", setting_path),
            )
            with self.subTest(path=setting_path), self.settings(**settings):
                msg = self.warning_message % (msg, "STATICFILES_DIRS")
                self.assertEqual(
                    check_cache_location_not_exposed(None),
                    [
                        Warning(msg, id="caches.W002"),
                    ],
                )