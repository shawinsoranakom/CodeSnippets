def test_templatetag10(self):
        output = self.engine.render_to_string("templatetag10")
        self.assertEqual(output, "}}")