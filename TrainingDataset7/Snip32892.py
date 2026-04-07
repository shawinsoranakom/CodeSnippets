def test_invalid_args(self):
        """Fail silently if invalid lookups are passed."""
        self.assertEqual(dictsort([{}], "._private"), "")
        self.assertEqual(dictsort([{"_private": "test"}], "_private"), "")
        self.assertEqual(
            dictsort([{"nested": {"_private": "test"}}], "nested._private"), ""
        )