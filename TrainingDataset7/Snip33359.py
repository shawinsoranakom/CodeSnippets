def test_syntax_error_missing_assignment(self, tag_name):
        msg = "No argument provided to the '{}' tag for the as option.".format(tag_name)
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")