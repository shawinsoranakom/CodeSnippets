def test_generates_on_usage(self):
        generated_tokens = []
        nonce = LazyNonce()
        self.assertFalse(nonce)
        self.assertIs(nonce._wrapped, empty)

        def memento_token_urlsafe(size):
            generated_tokens.append(result := token_urlsafe(size))
            return result

        with patch("django.utils.csp.secrets.token_urlsafe", memento_token_urlsafe):
            # Force usage, similar to template rendering, to generate the
            # nonce.
            val = str(nonce)

        self.assertTrue(nonce)
        self.assertEqual(nonce, val)
        self.assertIsInstance(nonce, str)
        self.assertEqual(repr(nonce), f"<LazyNonce: '{nonce}'>")
        self.assertEqual(len(val), 22)  # Based on secrets.token_urlsafe of 16 bytes.
        self.assertEqual(generated_tokens, [nonce])
        # Also test the wrapped value.
        self.assertEqual(nonce._wrapped, val)