def test_partialdef_invalid_inline(self):
        error_msg = "The 'inline' argument does not have any parameters"
        for template_name in ("with_params", "uppercase"):
            with (
                self.subTest(template_name=template_name),
                self.assertRaisesMessage(TemplateSyntaxError, error_msg),
            ):
                self.engine.render_to_string(template_name)