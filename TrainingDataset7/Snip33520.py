def test_cycle_undefined(self):
        with self.assertRaisesMessage(
            TemplateSyntaxError, "Named cycle 'undefined' does not exist"
        ):
            self.engine.render_to_string("undefined_cycle")