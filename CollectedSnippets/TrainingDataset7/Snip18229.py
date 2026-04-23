def test_password_reset_done_view(self):
        response = PasswordResetDoneView.as_view()(self.request)
        self.assertContains(
            response, "<title>Password reset sent | Django site admin</title>"
        )
        self.assertContains(response, "<h1>Password reset sent</h1>")