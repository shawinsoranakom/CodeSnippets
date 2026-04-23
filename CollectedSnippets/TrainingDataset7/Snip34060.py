def test_widthratio09(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.render_to_string("widthratio09", {"a": 50, "b": 100})