def test_templatetag08(self):
        output = self.engine.render_to_string("templatetag08")
        self.assertEqual(output, "}")