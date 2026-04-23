def test_lorem_syntax(self):
        msg = "Incorrect format for 'lorem' tag"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("lorem_syntax_error")