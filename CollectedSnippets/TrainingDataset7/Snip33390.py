def test_autoescape_tag03(self):
        output = self.engine.render_to_string(
            "autoescape-tag03", {"first": "<b>hello</b>"}
        )
        self.assertEqual(output, "&lt;b&gt;hello&lt;/b&gt;")