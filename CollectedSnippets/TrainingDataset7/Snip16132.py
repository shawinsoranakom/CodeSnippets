def test_model_admin_default_delete_action(self):
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk, self.s2.pk],
            "action": "delete_selected",
            "index": 0,
        }
        delete_confirmation_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk, self.s2.pk],
            "action": "delete_selected",
            "post": "yes",
        }
        confirmation = self.client.post(
            reverse("admin:admin_views_subscriber_changelist"), action_data
        )
        self.assertIsInstance(confirmation, TemplateResponse)
        self.assertContains(
            confirmation, "Are you sure you want to delete the selected subscribers?"
        )
        self.assertContains(confirmation, "<h1>Delete multiple objects</h1>")
        self.assertContains(confirmation, "<h2>Summary</h2>")
        self.assertContains(confirmation, "<li>Subscribers: 2</li>")
        self.assertContains(confirmation, "<li>External subscribers: 1</li>")
        self.assertContains(confirmation, ACTION_CHECKBOX_NAME, count=2)
        with CaptureQueriesContext(connection) as ctx:
            self.client.post(
                reverse("admin:admin_views_subscriber_changelist"),
                delete_confirmation_data,
            )
        # Log entries are inserted in bulk.
        self.assertEqual(
            len(
                [
                    q["sql"]
                    for q in ctx.captured_queries
                    if q["sql"].startswith("INSERT")
                ]
            ),
            1,
        )
        self.assertEqual(Subscriber.objects.count(), 0)