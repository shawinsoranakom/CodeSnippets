def test_autoescape_tag10(self):
        output = self.engine.render_to_string("autoescape-tag10", {"safe": SafeClass()})
        self.assertEqual(output, "you &gt; me")