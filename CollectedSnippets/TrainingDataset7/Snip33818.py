def test_include_error05(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("include-error05")