def test_include_error06(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("include-error06")