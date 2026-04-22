def test_simplify_number(self):
        """Test streamlit.string_util.simplify_number."""

        self.assertEqual(string_util.simplify_number(100), "100")

        self.assertEqual(string_util.simplify_number(10000), "10k")

        self.assertEqual(string_util.simplify_number(1000000), "1m")

        self.assertEqual(string_util.simplify_number(1000000000), "1b")

        self.assertEqual(string_util.simplify_number(1000000000000), "1t")