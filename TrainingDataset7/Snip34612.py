def test_valid_form_with_template(self):
        "POST valid data to a form using multiple templates"
        post_data = {
            "text": "Hello World",
            "email": "foo@example.com",
            "value": 37,
            "single": "b",
            "multi": ("b", "c", "e"),
        }
        response = self.client.post("/form_view_with_template/", post_data)
        self.assertContains(response, "POST data OK")
        self.assertTemplateUsed(response, "form_view.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateNotUsed(response, "Valid POST Template")