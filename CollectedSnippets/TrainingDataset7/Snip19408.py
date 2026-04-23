def test_missing_secret_key(self):
        del settings.SECRET_KEY
        self.assertEqual(base.check_secret_key(None), [base.W009])