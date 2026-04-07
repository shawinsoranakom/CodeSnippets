def test_include_error10(self):
        context = Context({"failed_include": "include-fail2"})
        template = self.engine.get_template("include-error10")
        with self.assertRaises(TemplateSyntaxError):
            template.render(context)