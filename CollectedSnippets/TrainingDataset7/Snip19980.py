def assertMaskedSecretCorrect(self, masked_secret, secret):
        """Test that a string is a valid masked version of a secret."""
        self.assertEqual(len(masked_secret), CSRF_TOKEN_LENGTH)
        self.assertEqual(len(secret), CSRF_SECRET_LENGTH)
        self.assertTrue(
            set(masked_secret).issubset(set(CSRF_ALLOWED_CHARS)),
            msg=f"invalid characters in {masked_secret!r}",
        )
        actual = _unmask_cipher_token(masked_secret)
        self.assertEqual(actual, secret)