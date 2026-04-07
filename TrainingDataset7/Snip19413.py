def test_okay_secret_key_fallbacks(self):
        self.assertEqual(
            len(settings.SECRET_KEY_FALLBACKS[0]),
            base.SECRET_KEY_MIN_LENGTH,
        )
        self.assertGreater(
            len(set(settings.SECRET_KEY_FALLBACKS[0])),
            base.SECRET_KEY_MIN_UNIQUE_CHARACTERS,
        )
        self.assertEqual(base.check_secret_key_fallbacks(None), [])