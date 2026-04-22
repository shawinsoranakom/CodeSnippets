def test_extract_args(self, name, input, expected):
        """Parse contents of outer parentheses from a string"""
        parsed = code_util.extract_args(input)

        self.assertEqual(parsed, expected)