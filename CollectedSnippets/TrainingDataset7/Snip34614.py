def test_form_error_with_template(self):
        "POST erroneous data to a form using multiple templates"
        post_data = {
            "text": "Hello World",
            "email": "not an email address",
            "value": 37,
            "single": "b",
            "multi": ("b", "c", "e"),
        }
        response = self.client.post("/form_view_with_template/", post_data)
        self.assertContains(response, "POST data has errors")
        self.assertTemplateUsed(response, "form_view.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateNotUsed(response, "Invalid POST Template")

        self.assertFormError(
            response.context["form"], "email", "Enter a valid email address."
        )