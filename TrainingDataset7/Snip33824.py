def test_include_error09(self):
        context = Context({"failed_include": "include-fail1"})
        template = self.engine.get_template("include-error09")
        with self.assertRaises(RuntimeError):
            template.render(context)