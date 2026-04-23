def test_user_message_on_none_selected(self):
        """
        User sees a warning when 'Go' is pressed and no items are selected.
        """
        action_data = {
            ACTION_CHECKBOX_NAME: [],
            "action": "delete_selected",
            "index": 0,
        }
        url = reverse("admin:admin_views_subscriber_changelist")
        response = self.client.post(url, action_data)
        self.assertRedirects(response, url, fetch_redirect_response=False)
        response = self.client.get(response.url)
        msg = (
            "Items must be selected in order to perform actions on them. No items have "
            "been changed."
        )
        self.assertContains(response, msg)
        self.assertEqual(Subscriber.objects.count(), 2)