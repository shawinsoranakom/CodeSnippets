def test_templatetag09(self):
        output = self.engine.render_to_string("templatetag09")
        self.assertEqual(output, "{{")