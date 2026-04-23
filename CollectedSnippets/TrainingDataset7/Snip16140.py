def test_custom_function_action_with_redirect(self):
        """Another custom action defined in a function."""
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk],
            "action": "redirect_to",
            "index": 0,
        }
        response = self.client.post(
            reverse("admin:admin_views_externalsubscriber_changelist"), action_data
        )
        self.assertEqual(response.status_code, 302)