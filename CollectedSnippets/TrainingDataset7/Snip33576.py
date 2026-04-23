def test_duplicate_block(self):
        msg = "'block' tag with name 'content' appears more than once"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("duplicate_block")