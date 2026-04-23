def test_get_connection(self):
        with self.assertDeprecatedIn70("'fail_silently'", "get_connection"):
            mail.get_connection(
                "django.core.mail.backends.dummy.EmailBackend",
                # Deprecated positional arg:
                True,
            )