def test_failure(self):
        msg = "response and/or template_name argument must be provided"
        with self.assertRaisesMessage(TypeError, msg):
            with self.assertTemplateUsed():
                pass

        msg = "No templates used to render the response"
        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed(""):
                pass

        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed(""):
                render_to_string("template_used/base.html")

        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed(template_name=""):
                pass

        msg = (
            "Template 'template_used/base.html' was not a template used to "
            "render the response. Actual template(s) used: "
            "template_used/alternative.html"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed("template_used/base.html"):
                render_to_string("template_used/alternative.html")