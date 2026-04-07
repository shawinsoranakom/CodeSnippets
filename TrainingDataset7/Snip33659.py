def test_invalid_in_keyword(self):
        msg = "'for' statements should use the format 'for x in y': for x from items"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("invalid_for_loop", {"items": (1, 2)})