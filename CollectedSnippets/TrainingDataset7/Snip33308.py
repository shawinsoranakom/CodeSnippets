def test_with_for(self, tag_name):
        msg = (
            f"'{tag_name}' doesn't allow other block tags (seen 'for b in [1, 2, 3]') "
            f"inside it"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template")