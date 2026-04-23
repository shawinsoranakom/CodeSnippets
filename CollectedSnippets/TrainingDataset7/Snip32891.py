def test_invalid_values(self):
        """
        If dictsort is passed something other than a list of dictionaries,
        fail silently.
        """
        self.assertEqual(dictsort([1, 2, 3], "age"), "")
        self.assertEqual(dictsort("Hello!", "age"), "")
        self.assertEqual(dictsort({"a": 1}, "age"), "")
        self.assertEqual(dictsort(1, "age"), "")