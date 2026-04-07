def test_unclosed_block2(self):
        msg = "Unclosed tag on line 1: 'if'. Looking for one of: elif, else, endif."
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")