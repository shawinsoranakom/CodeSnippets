def test_password_change(self):
        "Check the never-cache status of the password change view"
        self.client.logout()
        response = self.client.get(reverse("admin:password_change"))
        self.assertIsNone(get_max_age(response))