def test_password_reset_view(self):
        response = PasswordResetView.as_view(success_url="dummy/")(self.request)
        self.assertContains(
            response, "<title>Password reset | Django site admin</title>"
        )
        self.assertContains(response, "<h1>Password reset</h1>")