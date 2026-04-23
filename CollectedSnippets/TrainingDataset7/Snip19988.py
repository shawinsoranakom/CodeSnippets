def test_check_token_format_invalid(self):
        cases = [
            (64 * "*", "has invalid characters"),
            (16 * "a", "has incorrect length"),
        ]
        for token, expected_message in cases:
            with self.subTest(token=token):
                with self.assertRaisesMessage(InvalidTokenFormat, expected_message):
                    _check_token_format(token)