def test_widths(self):
        value = "something"
        for i in range(-1, len(value) + 1):
            with self.subTest(i=i):
                self.assertEqual(center(value, i), value)