def test_include04(self):
        template = self.engine.get_template("include04")
        with self.assertRaises(TemplateDoesNotExist):
            template.render(Context({}))