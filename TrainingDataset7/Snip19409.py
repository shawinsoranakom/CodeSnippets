def test_none_secret_key(self):
        self.assertEqual(base.check_secret_key(None), [base.W009])