def test_error_message_unexpected_template_used(self):
        msg = (
            "Template 'template_used/base.html' was not a template used to render "
            "the response. Actual template(s) used: template_used/alternative.html"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed("template_used/base.html"):
                render_to_string("template_used/alternative.html")