def test_invalid_url(self):
        self.assertEqual(
            check_csrf_trusted_origins(None),
            [
                Error(
                    "As of Django 4.0, the values in the CSRF_TRUSTED_ORIGINS "
                    "setting must start with a scheme (usually http:// or "
                    "https://) but found example.com. See the release notes for "
                    "details.",
                    id="4_0.E001",
                )
            ],
        )