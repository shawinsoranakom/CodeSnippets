def test_custom_function_mail_action(self):
        """A custom action may be defined in a function."""
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk],
            "action": "external_mail",
            "index": 0,
        }
        self.client.post(
            reverse("admin:admin_views_externalsubscriber_changelist"), action_data
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Greetings from a function action")