def test_low_entropy_secret_key(self):
        self.assertGreater(len(settings.SECRET_KEY), base.SECRET_KEY_MIN_LENGTH)
        self.assertLess(
            len(set(settings.SECRET_KEY)), base.SECRET_KEY_MIN_UNIQUE_CHARACTERS
        )
        self.assertEqual(base.check_secret_key(None), [base.W009])