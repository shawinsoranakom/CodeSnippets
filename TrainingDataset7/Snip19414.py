def test_no_secret_key_fallbacks(self):
        with self.settings(SECRET_KEY_FALLBACKS=None):
            del settings.SECRET_KEY_FALLBACKS
            self.assertEqual(
                base.check_secret_key_fallbacks(None),
                [
                    Warning(base.W025.msg % "SECRET_KEY_FALLBACKS", id=base.W025.id),
                ],
            )