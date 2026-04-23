def test_model_admin_no_delete_permission(self):
        """
        Permission is denied if the user doesn't have delete permission for the
        model (Subscriber).
        """
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk],
            "action": "delete_selected",
        }
        url = reverse("admin:admin_views_subscriber_changelist")
        response = self.client.post(url, action_data)
        self.assertRedirects(response, url, fetch_redirect_response=False)
        response = self.client.get(response.url)
        self.assertContains(response, "No action selected.")