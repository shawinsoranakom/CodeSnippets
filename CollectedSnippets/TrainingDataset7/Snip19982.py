def test_unmask_cipher_token(self):
        cases = [
            (TEST_SECRET, MASKED_TEST_SECRET1),
            (TEST_SECRET, MASKED_TEST_SECRET2),
            (
                32 * "a",
                "vFioG3XOLyGyGsPRFyB9iYUs341ufzIEvFioG3XOLyGyGsPRFyB9iYUs341ufzIE",
            ),
            (32 * "a", 64 * "a"),
            (32 * "a", 64 * "b"),
            (32 * "b", 32 * "a" + 32 * "b"),
            (32 * "b", 32 * "b" + 32 * "c"),
            (32 * "c", 32 * "a" + 32 * "c"),
        ]
        for secret, masked_secret in cases:
            with self.subTest(masked_secret=masked_secret):
                actual = _unmask_cipher_token(masked_secret)
                self.assertEqual(actual, secret)