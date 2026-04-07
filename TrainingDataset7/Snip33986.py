def test_templatetag01(self):
        output = self.engine.render_to_string("templatetag01")
        self.assertEqual(output, "{%")