def test_custom_function_action_no_perm_response(self):
        """A custom action may returns an HttpResponse with a 403 code."""
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk],
            "action": "no_perm",
            "index": 0,
        }
        response = self.client.post(
            reverse("admin:admin_views_externalsubscriber_changelist"), action_data
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, b"No permission to perform this action")