def test_floats(self):
        self.assertEqual(pluralize(0.5), "s")
        self.assertEqual(pluralize(1.5), "s")