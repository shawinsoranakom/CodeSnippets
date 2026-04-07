def test_syntax_error_no_arguments(self, tag_name):
        msg = "'{}' takes at least one argument".format(tag_name)
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")