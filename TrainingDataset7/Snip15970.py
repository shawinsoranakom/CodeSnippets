def test_flatten(self):
        flat_all = ["url", "title", "content", "sites"]
        inputs = (
            ((), []),
            (("url", "title", ("content", "sites")), flat_all),
            (("url", "title", "content", "sites"), flat_all),
            ((("url", "title"), ("content", "sites")), flat_all),
        )
        for orig, expected in inputs:
            self.assertEqual(flatten(orig), expected)