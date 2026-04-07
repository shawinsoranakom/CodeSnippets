def test_user_not_change(self):
        response = self.client.post(
            reverse("auth_test_admin:auth_user_change", args=(self.admin.pk,)),
            self.get_user_data(self.admin),
        )
        self.assertRedirects(response, reverse("auth_test_admin:auth_user_changelist"))
        row = LogEntry.objects.latest("id")
        self.assertEqual(row.get_change_message(), "No fields changed.")