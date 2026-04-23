def test_autoescape_tag08(self):
        """
        Literal string arguments to filters, if used in the result, are safe.
        """
        output = self.engine.render_to_string("autoescape-tag08", {"var": None})
        self.assertEqual(output, ' endquote" hah')