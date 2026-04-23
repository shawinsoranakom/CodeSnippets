def test_else_if_tag_error01(self):
        error_message = 'Malformed template tag at line 1: "else if foo is not bar"'
        with self.assertRaisesMessage(TemplateSyntaxError, error_message):
            self.engine.get_template("else-if-tag-error01")