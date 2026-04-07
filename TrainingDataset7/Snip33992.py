def test_templatetag07(self):
        output = self.engine.render_to_string("templatetag07")
        self.assertEqual(output, "{")