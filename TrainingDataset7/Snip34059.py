def test_widthratio08(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("widthratio08")