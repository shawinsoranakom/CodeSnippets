def test_autoescape_stringfilter02(self):
        output = self.engine.render_to_string(
            "autoescape-stringfilter02", {"unsafe": UnsafeClass()}
        )
        self.assertEqual(output, "You & me")