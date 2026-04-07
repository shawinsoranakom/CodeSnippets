def test_if_tag_error10(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template("if-tag-error10")