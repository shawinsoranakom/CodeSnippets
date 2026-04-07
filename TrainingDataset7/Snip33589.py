def test_filter_syntax11(self):
        """
        Variable as argument
        """
        output = self.engine.render_to_string(
            "filter-syntax11", {"var": None, "var2": "happy"}
        )
        self.assertEqual(output, "happy")