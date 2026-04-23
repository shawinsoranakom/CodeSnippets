def test_autoescape_tag05(self):
        output = self.engine.render_to_string(
            "autoescape-tag05", {"first": "<b>first</b>"}
        )
        self.assertEqual(output, "&lt;b&gt;first&lt;/b&gt;")