def test_inheritance_empty(self):
        with self.assertRaisesMessage(
            TemplateSyntaxError, "'extends' takes one argument"
        ):
            self.engine.render_to_string("inheritance_empty")