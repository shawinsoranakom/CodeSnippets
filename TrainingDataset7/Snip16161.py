def test_model_admin_no_delete_permission_externalsubscriber(self):
        """
        Permission is denied if the user doesn't have delete permission for a
        related model (ExternalSubscriber).
        """
        permission = Permission.objects.get(codename="delete_subscriber")
        self.user.user_permissions.add(permission)
        delete_confirmation_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk, self.s2.pk],
            "action": "delete_selected",
            "post": "yes",
        }
        response = self.client.post(
            reverse("admin:admin_views_subscriber_changelist"), delete_confirmation_data
        )
        self.assertEqual(response.status_code, 403)