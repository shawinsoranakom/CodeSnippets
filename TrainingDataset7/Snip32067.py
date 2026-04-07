def test_add_script_name_prefix(self):
        tests = (
            # Relative paths.
            ("/somesubpath", "path/", "/somesubpath/path/"),
            ("/somesubpath/", "path/", "/somesubpath/path/"),
            ("/", "path/", "/path/"),
            # Invalid URLs.
            (
                "/somesubpath/",
                "htp://myhost.com/path/",
                "/somesubpath/htp://myhost.com/path/",
            ),
            # Blank settings.
            ("/somesubpath/", "", "/somesubpath/"),
        )
        for setting in ("MEDIA_URL", "STATIC_URL"):
            for script_name, path, expected_path in tests:
                new_settings = {setting: path}
                with self.settings(**new_settings):
                    with self.subTest(script_name=script_name, **new_settings):
                        try:
                            self.set_script_name(script_name)
                            self.assertEqual(getattr(settings, setting), expected_path)
                        finally:
                            clear_script_prefix()