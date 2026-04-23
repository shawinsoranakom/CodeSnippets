def test_format(self):
        self.assertEqual(stringformat(1, "03d"), "001")
        self.assertEqual(stringformat([1, None], "s"), "[1, None]")
        self.assertEqual(stringformat((1, 2, 3), "s"), "(1, 2, 3)")
        self.assertEqual(stringformat((1,), "s"), "(1,)")
        self.assertEqual(stringformat({1, 2}, "s"), "{1, 2}")
        self.assertEqual(stringformat({1: 2, 2: 3}, "s"), "{1: 2, 2: 3}")