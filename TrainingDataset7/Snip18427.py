def test_user_change_different_user_password(self):
        u = User.objects.get(email="staffmember@example.com")
        response = self.client.post(
            reverse("auth_test_admin:auth_user_password_change", args=(u.pk,)),
            {
                "password1": "password1",
                "password2": "password1",
            },
        )
        self.assertRedirects(
            response, reverse("auth_test_admin:auth_user_change", args=(u.pk,))
        )
        row = LogEntry.objects.latest("id")
        self.assertEqual(row.user_id, self.admin.pk)
        self.assertEqual(row.object_id, str(u.pk))
        self.assertEqual(row.get_change_message(), "Changed password.")