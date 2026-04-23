def test_lists(self):
        self.assertEqual(pluralize([1]), "")
        self.assertEqual(pluralize([]), "s")
        self.assertEqual(pluralize([1, 2, 3]), "s")