def test_autoescape_tag07(self):
        output = self.engine.render_to_string(
            "autoescape-tag07", {"first": mark_safe("<b>Apple</b>")}
        )
        self.assertEqual(output, "<b>Apple</b>")