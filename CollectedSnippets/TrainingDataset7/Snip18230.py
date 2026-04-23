def test_password_reset_confirm_view_invalid_token(self):
        # PasswordResetConfirmView invalid token
        client = PasswordResetConfirmClient()
        url = reverse(
            "password_reset_confirm", kwargs={"uidb64": "Bad", "token": "Bad-Token"}
        )
        response = client.get(url)
        self.assertContains(
            response, "<title>Password reset unsuccessful | Django site admin</title>"
        )
        self.assertContains(response, "<h1>Password reset unsuccessful</h1>")