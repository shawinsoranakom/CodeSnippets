def test_variable_twice(self):
        with self.assertRaisesMessage(
            TemplateSyntaxError, "The 'with' option was specified more than once"
        ):
            self.engine.render_to_string("template", {"foo": "bar"})