def test_valid_form_with_hints(self):
        "GET a form, providing hints in the GET data"
        hints = {"text": "Hello World", "multi": ("b", "c", "e")}
        response = self.client.get("/form_view/", data=hints)
        # The multi-value data has been rolled out ok
        self.assertContains(response, "Select a valid choice.", 0)
        self.assertTemplateUsed(response, "Form GET Template")