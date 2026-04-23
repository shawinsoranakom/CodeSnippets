def test_password_reset_confirm_view_error_title(self):
        client = PasswordResetConfirmClient()
        default_token_generator = PasswordResetTokenGenerator()
        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(str(self.user.pk).encode())
        url = reverse(
            "password_reset_confirm", kwargs={"uidb64": uidb64, "token": token}
        )
        response = client.post(url, {})
        self.assertContains(
            response, "<title>Error: Enter new password | Django site admin</title>"
        )