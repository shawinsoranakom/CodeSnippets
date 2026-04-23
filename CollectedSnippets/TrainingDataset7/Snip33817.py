def test_include_error04(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("include-error04")