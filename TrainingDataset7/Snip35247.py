def test_template_used_fail_non_partial(self):
        msg = (
            "Template 'template_used/base.html#template_used/base.html' was not a "
            "template used to render the response."
        )
        with (
            self.assertRaisesMessage(AssertionError, msg),
            self.assertTemplateUsed("template_used/base.html#template_used/base.html"),
        ):
            render_to_string("template_used/base.html")