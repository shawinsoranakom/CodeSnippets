def test_low_length_secret_key_fallbacks(self):
        self.assertEqual(
            len(settings.SECRET_KEY_FALLBACKS[0]),
            base.SECRET_KEY_MIN_LENGTH - 1,
        )
        self.assertEqual(
            base.check_secret_key_fallbacks(None),
            [
                Warning(base.W025.msg % "SECRET_KEY_FALLBACKS[0]", id=base.W025.id),
            ],
        )