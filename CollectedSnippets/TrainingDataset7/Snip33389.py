def test_autoescape_tag02(self):
        output = self.engine.render_to_string(
            "autoescape-tag02", {"first": "<b>hello</b>"}
        )
        self.assertEqual(output, "<b>hello</b>")