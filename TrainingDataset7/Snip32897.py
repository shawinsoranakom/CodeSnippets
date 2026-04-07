def test_invalid_args(self):
        """Fail silently if invalid lookups are passed."""
        self.assertEqual(dictsortreversed([{}], "._private"), "")
        self.assertEqual(dictsortreversed([{"_private": "test"}], "_private"), "")
        self.assertEqual(
            dictsortreversed([{"nested": {"_private": "test"}}], "nested._private"), ""
        )