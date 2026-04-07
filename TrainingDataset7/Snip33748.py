def test_if_tag_error01(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("if-tag-error01")