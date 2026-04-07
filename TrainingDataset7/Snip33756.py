def test_if_tag_error09(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("if-tag-error09")