def test_include_error01(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("include-error01")