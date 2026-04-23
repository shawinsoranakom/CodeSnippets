def test_not_prefixed(self):
        # Don't add SCRIPT_NAME prefix to absolute paths, URLs, or None.
        tests = (
            "/path/",
            "http://myhost.com/path/",
            "http://myhost/path/",
            "https://myhost/path/",
            None,
        )
        for setting in ("MEDIA_URL", "STATIC_URL"):
            for path in tests:
                new_settings = {setting: path}
                with self.settings(**new_settings):
                    for script_name in ["/somesubpath", "/somesubpath/", "/", "", None]:
                        with self.subTest(script_name=script_name, **new_settings):
                            try:
                                self.set_script_name(script_name)
                                self.assertEqual(getattr(settings, setting), path)
                            finally:
                                clear_script_prefix()