def test_repr(self):
        nonce = LazyNonce()
        self.assertEqual(repr(nonce), f"<LazyNonce: {repr(generate_nonce)}>")

        str(nonce)  # Force nonce generation.
        self.assertRegex(repr(nonce), r"<LazyNonce: '[^']+'>")