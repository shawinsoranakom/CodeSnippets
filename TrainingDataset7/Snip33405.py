def test_no_arg(self):
        msg = "'autoescape' tag requires exactly one argument."
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string(
                "autoescape-incorrect-arg", {"var": {"key": "this & that"}}
            )