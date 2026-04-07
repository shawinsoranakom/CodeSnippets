def test_popup_actions(self):
        """Actions aren't shown in popups."""
        changelist_url = reverse("admin:admin_views_subscriber_changelist")
        response = self.client.get(changelist_url)
        self.assertIsNotNone(response.context["action_form"])
        response = self.client.get(changelist_url + "?%s" % IS_POPUP_VAR)
        self.assertIsNone(response.context["action_form"])