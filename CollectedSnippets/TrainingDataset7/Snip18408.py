def test_logout_with_named_redirect(self):
        "Logout resolves names or URLs passed as next_page."
        self.login()
        response = self.client.post("/logout/next_page/named/")
        self.assertRedirects(
            response, "/password_reset/", fetch_redirect_response=False
        )
        self.confirm_logged_out()