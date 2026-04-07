def test_filter_syntax17(self):
        """
        Empty strings can be passed as arguments to filters
        """
        output = self.engine.render_to_string(
            "filter-syntax17", {"var": ["a", "b", "c"]}
        )
        self.assertEqual(output, "abc")