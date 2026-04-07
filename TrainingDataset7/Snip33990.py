def test_templatetag05(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("templatetag05")