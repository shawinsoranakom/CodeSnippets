def test_no_context(self):
        "Template usage assertions work then templates aren't in use"
        response = self.client.get("/no_template_view/")

        # The no template case doesn't mess with the template assertions
        self.assertTemplateNotUsed(response, "GET Template")

        msg = "No templates used to render the response"
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertTemplateUsed(response, "GET Template")

        msg = "No templates used to render the response"
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertTemplateUsed(response, "GET Template", msg_prefix="abc")

        msg = "No templates used to render the response"
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertTemplateUsed(response, "GET Template", count=2)