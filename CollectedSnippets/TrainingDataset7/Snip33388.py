def test_autoescape_tag01(self):
        output = self.engine.render_to_string("autoescape-tag01")
        self.assertEqual(output, "hello")