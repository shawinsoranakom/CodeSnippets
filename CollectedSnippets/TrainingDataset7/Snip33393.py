def test_autoescape_tag06(self):
        output = self.engine.render_to_string(
            "autoescape-tag06", {"first": mark_safe("<b>first</b>")}
        )
        self.assertEqual(output, "<b>first</b>")