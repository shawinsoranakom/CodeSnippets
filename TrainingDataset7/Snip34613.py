def test_incomplete_data_form_with_template(self):
        "POST incomplete data to a form using multiple templates"
        post_data = {"text": "Hello World", "value": 37}
        response = self.client.post("/form_view_with_template/", post_data)
        self.assertContains(response, "POST data has errors")
        self.assertTemplateUsed(response, "form_view.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateNotUsed(response, "Invalid POST Template")
        form = response.context["form"]
        self.assertFormError(form, "email", "This field is required.")
        self.assertFormError(form, "single", "This field is required.")
        self.assertFormError(form, "multi", "This field is required.")