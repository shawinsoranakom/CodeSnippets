def test_too_many_digits_to_render(self):
        cases = [
            "1e200",
            "1E200",
            "1E10000000000000000",
            "-1E10000000000000000",
            "1e10000000000000000",
            "-1e10000000000000000",
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assertEqual(floatformat(value), value)