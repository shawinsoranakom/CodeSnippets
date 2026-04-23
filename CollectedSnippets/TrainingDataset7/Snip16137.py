def test_delete_queryset_hook(self):
        delete_confirmation_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk, self.s2.pk],
            "action": "delete_selected",
            "post": "yes",
            "index": 0,
        }
        SubscriberAdmin.overridden = False
        self.client.post(
            reverse("admin:admin_views_subscriber_changelist"), delete_confirmation_data
        )
        # SubscriberAdmin.delete_queryset() sets overridden to True.
        self.assertIs(SubscriberAdmin.overridden, True)
        self.assertEqual(Subscriber.objects.count(), 0)