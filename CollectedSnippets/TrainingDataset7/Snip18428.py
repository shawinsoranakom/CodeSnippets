def test_password_change_bad_url(self):
        response = self.client.get(
            reverse("auth_test_admin:auth_user_password_change", args=("foobar",))
        )
        self.assertEqual(response.status_code, 404)