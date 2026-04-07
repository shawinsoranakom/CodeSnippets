def test_template_used_fail(self):
        msg = "Template 'hello' was not a template used to render the response."
        with (
            self.assertRaisesMessage(AssertionError, msg),
            self.assertTemplateUsed("hello"),
        ):
            render_to_string("template_used/base.html")