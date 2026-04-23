def test_does_token_match_wrong_token_length(self):
        with self.assertRaises(AssertionError):
            _does_token_match(16 * "a", TEST_SECRET)