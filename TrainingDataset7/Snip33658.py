def test_invalid_arg(self):
        msg = "'for' statements should have at least four words: for x items"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("invalid_for_loop", {"items": (1, 2)})