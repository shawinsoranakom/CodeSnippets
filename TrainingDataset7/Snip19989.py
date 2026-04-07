def test_does_token_match(self):
        cases = [
            # Masked tokens match.
            ((MASKED_TEST_SECRET1, TEST_SECRET), True),
            ((MASKED_TEST_SECRET2, TEST_SECRET), True),
            ((64 * "a", _unmask_cipher_token(64 * "a")), True),
            # Unmasked tokens match.
            ((TEST_SECRET, TEST_SECRET), True),
            ((32 * "a", 32 * "a"), True),
            # Incorrect tokens don't match.
            ((32 * "a", TEST_SECRET), False),
            ((64 * "a", TEST_SECRET), False),
        ]
        for (token, secret), expected in cases:
            with self.subTest(token=token, secret=secret):
                actual = _does_token_match(token, secret)
                self.assertIs(actual, expected)