def test_templatetag06(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("templatetag06")