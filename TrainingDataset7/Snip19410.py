def test_insecure_secret_key(self):
        self.assertEqual(base.check_secret_key(None), [base.W009])