def test_default_delete_action_nonexistent_pk(self):
        self.assertFalse(Subscriber.objects.filter(id=9998).exists())
        action_data = {
            ACTION_CHECKBOX_NAME: ["9998"],
            "action": "delete_selected",
            "index": 0,
        }
        response = self.client.post(
            reverse("admin:admin_views_subscriber_changelist"), action_data
        )
        self.assertContains(
            response, "Are you sure you want to delete the selected subscribers?"
        )
        self.assertContains(response, "<ul></ul>", html=True)