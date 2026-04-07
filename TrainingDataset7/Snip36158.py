def test_returns_same_value(self):
        nonce = LazyNonce()
        first = str(nonce)
        second = str(nonce)

        self.assertEqual(first, second)