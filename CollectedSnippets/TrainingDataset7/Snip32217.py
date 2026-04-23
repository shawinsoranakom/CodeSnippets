def test_base62(self):
        tests = [-(10**10), 10**10, 1620378259, *range(-100, 100)]
        for i in tests:
            self.assertEqual(i, signing.b62_decode(signing.b62_encode(i)))