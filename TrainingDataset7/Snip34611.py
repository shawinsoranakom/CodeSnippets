def test_form_error(self):
        "POST erroneous data to a form"
        post_data = {
            "text": "Hello World",
            "email": "not an email address",
            "value": 37,
            "single": "b",
            "multi": ("b", "c", "e"),
        }
        response = self.client.post("/form_view/", post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Invalid POST Template")

        self.assertFormError(
            response.context["form"], "email", "Enter a valid email address."
        )