def test_negative_numbers(self):
        tests = [
            (-1, "-1\xa0byte"),
            (-100, "-100\xa0bytes"),
            (-1024 * 1024 * 50, "-50.0\xa0MB"),
        ]
        for value, expected in tests:
            with self.subTest(value=value):
                self.assertEqual(filesizeformat(value), expected)