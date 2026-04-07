def test_widthratio18(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("widthratio18")