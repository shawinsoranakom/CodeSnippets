def test_multiple_actions_form(self):
        """
        Actions come from the form whose submit button was pressed (#10618).
        """
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk],
            # Two different actions selected on the two forms...
            "action": ["external_mail", "delete_selected"],
            # ...but "go" was clicked on the top form.
            "index": 0,
        }
        self.client.post(
            reverse("admin:admin_views_externalsubscriber_changelist"), action_data
        )
        # The action sends mail rather than deletes.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Greetings from a function action")