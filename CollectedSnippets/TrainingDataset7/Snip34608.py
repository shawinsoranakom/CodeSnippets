def test_valid_form(self):
        "POST valid data to a form"
        post_data = {
            "text": "Hello World",
            "email": "foo@example.com",
            "value": 37,
            "single": "b",
            "multi": ("b", "c", "e"),
        }
        response = self.client.post("/form_view/", post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Valid POST Template")