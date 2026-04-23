def test_admin_password_change(self):
        u = UUIDUser.objects.create_superuser(
            username="uuid", email="foo@bar.com", password="test"
        )
        self.assertTrue(self.client.login(username="uuid", password="test"))

        user_change_url = reverse(
            "custom_user_admin:auth_tests_uuiduser_change", args=(u.pk,)
        )
        response = self.client.get(user_change_url)
        self.assertEqual(response.status_code, 200)

        password_change_url = reverse(
            "custom_user_admin:auth_user_password_change", args=(u.pk,)
        )
        response = self.client.get(password_change_url)
        # The action attribute is omitted.
        self.assertContains(response, '<form method="post" id="uuiduser_form">')

        # A LogEntry is created with pk=1 which breaks a FK constraint on MySQL
        with connection.constraint_checks_disabled():
            response = self.client.post(
                password_change_url,
                {
                    "password1": "password1",
                    "password2": "password1",
                },
            )
        self.assertRedirects(response, user_change_url)
        row = LogEntry.objects.latest("id")
        self.assertEqual(row.user_id, 1)  # hardcoded in CustomUserAdmin.log_change()
        self.assertEqual(row.object_id, str(u.pk))
        self.assertEqual(row.get_change_message(), "Changed password.")

        # The LogEntry.user column isn't altered to a UUID type so it's set to
        # an integer manually in CustomUserAdmin to avoid an error. To avoid a
        # constraint error, delete the entry before constraints are checked
        # after the test.
        row.delete()