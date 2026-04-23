def test_user_message_on_no_action(self):
        """
        User sees a warning when 'Go' is pressed and no action is selected.
        """
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk, self.s2.pk],
            "action": "",
            "index": 0,
        }
        url = reverse("admin:admin_views_subscriber_changelist")
        response = self.client.post(url, action_data)
        self.assertRedirects(response, url, fetch_redirect_response=False)
        response = self.client.get(response.url)
        self.assertContains(response, "No action selected.")
        self.assertEqual(Subscriber.objects.count(), 2)