def test_integers(self):
        self.assertEqual(pluralize(1), "")
        self.assertEqual(pluralize(0), "s")
        self.assertEqual(pluralize(2), "s")