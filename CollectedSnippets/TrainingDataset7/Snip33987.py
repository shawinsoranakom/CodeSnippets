def test_templatetag02(self):
        output = self.engine.render_to_string("templatetag02")
        self.assertEqual(output, "%}")