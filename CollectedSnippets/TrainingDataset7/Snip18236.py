def test_password_reset_change_view(self):
        response = PasswordChangeView.as_view(success_url="dummy/")(self.request)
        self.assertContains(
            response, "<title>Password change | Django site admin</title>"
        )
        self.assertContains(response, "<h1>Password change</h1>")