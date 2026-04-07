def test_title_output(self):
        title, description, metadata = parse_docstring(self.docstring)
        title_output = parse_rst(title, "model", "model:admindocs")
        self.assertIn("TITLE", title_output)
        title_rendered = (
            "<p>This __doc__ output is required for testing. I copied this "
            'example from\n<a class="reference external" '
            'href="/admindocs/models/admindocs/">admindocs</a> documentation. '
            "(TITLE)</p>\n"
        )
        self.assertHTMLEqual(title_output, title_rendered)