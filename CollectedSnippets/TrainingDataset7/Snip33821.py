def test_include_fail2(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("include-fail2")