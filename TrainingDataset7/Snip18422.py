def test_changelist_disallows_password_lookups(self):
        # A lookup that tries to filter on password isn't OK
        with self.assertLogs("django.security.DisallowedModelAdminLookup", "ERROR"):
            response = self.client.get(
                reverse("auth_test_admin:auth_user_changelist")
                + "?password__startswith=sha1$"
            )
        self.assertEqual(response.status_code, 400)