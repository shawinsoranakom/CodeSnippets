def test_mask_cipher_secret(self):
        cases = [
            32 * "a",
            TEST_SECRET,
            "da4SrUiHJYoJ0HYQ0vcgisoIuFOxx4ER",
        ]
        for secret in cases:
            with self.subTest(secret=secret):
                masked = _mask_cipher_secret(secret)
                self.assertMaskedSecretCorrect(masked, secret)