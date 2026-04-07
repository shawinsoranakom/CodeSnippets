def test_password_reset_complete_view(self):
        response = PasswordResetCompleteView.as_view()(self.request)
        self.assertContains(
            response, "<title>Password reset complete | Django site admin</title>"
        )
        self.assertContains(response, "<h1>Password reset complete</h1>")