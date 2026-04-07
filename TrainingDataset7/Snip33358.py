def test_syntax_error_bad_option(self, tag_name):
        msg = "Unknown argument for '{}' tag: 'badoption'".format(tag_name)
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")