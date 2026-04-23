def test_no_for_as(self):
        msg = "'get_language_info' requires 'for string as variable' (got [])"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")