def test_password_reset_view_error_title(self):
        response = self.client.post(reverse("password_reset"), {})
        self.assertContains(
            response, "<title>Error: Password reset | Django site admin</title>"
        )