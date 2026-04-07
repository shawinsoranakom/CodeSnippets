def test_model_admin_custom_action(self):
        """A custom action defined in a ModelAdmin method."""
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk],
            "action": "mail_admin",
            "index": 0,
        }
        self.client.post(
            reverse("admin:admin_views_subscriber_changelist"), action_data
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Greetings from a ModelAdmin action")