def test_non_matching_string(self):
        self.assertEqual(
            cut("a string to be mangled", "strings"), "a string to be mangled"
        )