def test_include_error08(self):
        template = self.engine.get_template("include-error08")
        with self.assertRaises(TemplateSyntaxError):
            template.render(Context())