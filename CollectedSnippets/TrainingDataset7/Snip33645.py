def test_unpack_vertical_bar(self):
        msg = "'for' tag received an invalid argument: for k|upper in items"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("vertical-bar", {"items": (1, 2)})