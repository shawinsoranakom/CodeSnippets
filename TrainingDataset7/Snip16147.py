def test_action_column_class(self):
        """The checkbox column class is present in the response."""
        response = self.client.get(reverse("admin:admin_views_subscriber_changelist"))
        self.assertIsNotNone(response.context["action_form"])
        self.assertContains(response, "action-checkbox-column")