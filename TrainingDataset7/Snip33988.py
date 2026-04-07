def test_templatetag03(self):
        output = self.engine.render_to_string("templatetag03")
        self.assertEqual(output, "{{")