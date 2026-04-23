def test_password_change_done(self):
        "Check the never-cache status of the password change done view"
        response = self.client.get(reverse("admin:password_change_done"))
        self.assertIsNone(get_max_age(response))