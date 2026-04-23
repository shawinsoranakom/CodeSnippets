def test_invalid_values(self):
        """
        If dictsortreversed is passed something other than a list of
        dictionaries, fail silently.
        """
        self.assertEqual(dictsortreversed([1, 2, 3], "age"), "")
        self.assertEqual(dictsortreversed("Hello!", "age"), "")
        self.assertEqual(dictsortreversed({"a": 1}, "age"), "")
        self.assertEqual(dictsortreversed(1, "age"), "")