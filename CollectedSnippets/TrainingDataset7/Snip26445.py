def test_context_processor_message_levels(self):
        show_url = reverse("show_template_response")
        response = self.client.get(show_url)

        self.assertIn("DEFAULT_MESSAGE_LEVELS", response.context)
        self.assertEqual(response.context["DEFAULT_MESSAGE_LEVELS"], DEFAULT_LEVELS)