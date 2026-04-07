def test_incomplete_data_form(self):
        "POST incomplete data to a form"
        post_data = {"text": "Hello World", "value": 37}
        response = self.client.post("/form_view/", post_data)
        self.assertContains(response, "This field is required.", 3)
        self.assertTemplateUsed(response, "Invalid POST Template")
        form = response.context["form"]
        self.assertFormError(form, "email", "This field is required.")
        self.assertFormError(form, "single", "This field is required.")
        self.assertFormError(form, "multi", "This field is required.")