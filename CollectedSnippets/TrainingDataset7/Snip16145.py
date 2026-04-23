def test_model_without_action(self):
        """A ModelAdmin might not have any actions."""
        response = self.client.get(
            reverse("admin:admin_views_oldsubscriber_changelist")
        )
        self.assertIsNone(response.context["action_form"])
        self.assertNotContains(
            response,
            '<input type="checkbox" class="action-select"',
            msg_prefix="Found an unexpected action toggle checkboxbox in response",
        )
        self.assertNotContains(response, '<input type="checkbox" class="action-select"')