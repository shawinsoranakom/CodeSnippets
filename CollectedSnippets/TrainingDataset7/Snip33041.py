def test_suffixes(self):
        self.assertEqual(pluralize(1, "es"), "")
        self.assertEqual(pluralize(0, "es"), "es")
        self.assertEqual(pluralize(2, "es"), "es")
        self.assertEqual(pluralize(1, "y,ies"), "y")
        self.assertEqual(pluralize(0, "y,ies"), "ies")
        self.assertEqual(pluralize(2, "y,ies"), "ies")
        self.assertEqual(pluralize(0, "y,ies,error"), "")