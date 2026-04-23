def test_error_message_no_template_used(self):
        msg = "No templates used to render the response"
        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed("template_used/base.html"):
                pass

        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed(template_name="template_used/base.html"):
                pass

        with self.assertRaisesMessage(AssertionError, msg):
            response = self.client.get("/test_utils/no_template_used/")
            self.assertTemplateUsed(response, "template_used/base.html")

        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed("template_used/base.html"):
                self.client.get("/test_utils/no_template_used/")

        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed("template_used/base.html"):
                template = Template("template_used/alternative.html", name=None)
                template.render(Context())