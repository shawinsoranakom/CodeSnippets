def test_low_entropy_secret_key_fallbacks(self):
        self.assertGreater(
            len(settings.SECRET_KEY_FALLBACKS[0]),
            base.SECRET_KEY_MIN_LENGTH,
        )
        self.assertLess(
            len(set(settings.SECRET_KEY_FALLBACKS[0])),
            base.SECRET_KEY_MIN_UNIQUE_CHARACTERS,
        )
        self.assertEqual(
            base.check_secret_key_fallbacks(None),
            [
                Warning(base.W025.msg % "SECRET_KEY_FALLBACKS[0]", id=base.W025.id),
            ],
        )