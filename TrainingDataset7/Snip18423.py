def test_user_change_email(self):
        data = self.get_user_data(self.admin)
        data["email"] = "new_" + data["email"]
        response = self.client.post(
            reverse("auth_test_admin:auth_user_change", args=(self.admin.pk,)), data
        )
        self.assertRedirects(response, reverse("auth_test_admin:auth_user_changelist"))
        row = LogEntry.objects.latest("id")
        self.assertEqual(row.get_change_message(), "Changed Email address.")