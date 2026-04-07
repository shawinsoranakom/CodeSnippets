def test_autoescape_tag09(self):
        output = self.engine.render_to_string(
            "autoescape-tag09", {"unsafe": UnsafeClass()}
        )
        self.assertEqual(output, "you &amp; me")