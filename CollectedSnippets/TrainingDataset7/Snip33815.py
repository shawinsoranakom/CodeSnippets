def test_include_error02(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("include-error02")