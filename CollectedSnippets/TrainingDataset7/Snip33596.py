def test_filter_syntax19(self):
        """
        Numbers as filter arguments should work
        """
        output = self.engine.render_to_string("filter-syntax19", {"var": "hello world"})
        self.assertEqual(output, "hello …")