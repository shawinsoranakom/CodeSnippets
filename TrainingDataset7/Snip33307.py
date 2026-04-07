def test_with_block(self, tag_name):
        msg = "'{}' doesn't allow other block tags (seen 'block b') inside it".format(
            tag_name
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")