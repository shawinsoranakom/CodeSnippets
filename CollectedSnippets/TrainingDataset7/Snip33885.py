def test_now_args(self):
        with self.assertRaisesMessage(
            TemplateSyntaxError, "'now' statement takes one argument"
        ):
            self.engine.render_to_string("no_args")