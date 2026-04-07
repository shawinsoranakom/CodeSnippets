def test_valid_variant_consistent_language_settings(self):
        tests = [
            # language + region.
            "fr-CA",
            "es-419",
            "de-at",
            # language + region + variant.
            "ca-ES-valencia",
        ]
        for tag in tests:
            with self.subTest(tag), self.settings(LANGUAGE_CODE=tag):
                self.assertEqual(check_language_settings_consistent(None), [])