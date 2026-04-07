def test_low_length_secret_key(self):
        self.assertEqual(len(settings.SECRET_KEY), base.SECRET_KEY_MIN_LENGTH - 1)
        self.assertEqual(base.check_secret_key(None), [base.W009])