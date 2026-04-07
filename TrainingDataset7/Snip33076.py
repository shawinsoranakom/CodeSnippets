def test_invalid(self):
        self.assertEqual(stringformat(1, "z"), "")
        self.assertEqual(stringformat(object(), "d"), "")
        self.assertEqual(stringformat(None, "d"), "")
        self.assertEqual(stringformat((1, 2, 3), "d"), "")