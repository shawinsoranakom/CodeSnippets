def test_autoescape_stringfilter03(self):
        output = self.engine.render_to_string(
            "autoescape-stringfilter03", {"safe": SafeClass()}
        )
        self.assertEqual(output, "You &gt; me")