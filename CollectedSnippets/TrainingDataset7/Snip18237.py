def test_password_change_done_view(self):
        response = PasswordChangeDoneView.as_view()(self.request)
        self.assertContains(
            response, "<title>Password change successful | Django site admin</title>"
        )
        self.assertContains(response, "<h1>Password change successful</h1>")