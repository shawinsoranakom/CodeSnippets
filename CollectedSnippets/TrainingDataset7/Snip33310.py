def test_no_args_with(self, tag_name):
        msg = "\"with\" in '{}' tag needs at least one keyword argument.".format(
            tag_name
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")