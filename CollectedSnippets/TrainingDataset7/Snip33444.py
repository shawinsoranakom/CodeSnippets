def test_unclosed_block(self):
        msg = "Unclosed tag on line 1: 'block'. Looking for one of: endblock."
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")