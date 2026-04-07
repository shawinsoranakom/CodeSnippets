def test_template_not_used_fail(self):
        msg = (
            "Template 'template_used/partials.html#hello' was used "
            "unexpectedly in rendering the response"
        )
        with (
            self.assertRaisesMessage(AssertionError, msg),
            self.assertTemplateNotUsed("template_used/partials.html#hello"),
        ):
            render_to_string("template_used/partials.html#hello")