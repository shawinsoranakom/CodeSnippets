def test_templatetag04(self):
        output = self.engine.render_to_string("templatetag04")
        self.assertEqual(output, "}}")