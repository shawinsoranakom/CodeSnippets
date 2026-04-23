def test_filter_syntax09(self):
        """
        Chained filters, with an argument to the first one
        """
        output = self.engine.render_to_string("filter-syntax09", {"var": "Foo"})
        self.assertEqual(output, "f")