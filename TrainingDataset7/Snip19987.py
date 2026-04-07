def test_check_token_format_valid(self):
        cases = [
            # A token of length CSRF_SECRET_LENGTH.
            TEST_SECRET,
            # A token of length CSRF_TOKEN_LENGTH.
            MASKED_TEST_SECRET1,
            64 * "a",
        ]
        for token in cases:
            with self.subTest(token=token):
                actual = _check_token_format(token)
                self.assertIsNone(actual)