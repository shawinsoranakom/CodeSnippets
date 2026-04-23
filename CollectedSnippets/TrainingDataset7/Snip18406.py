def test_logout_with_redirect_argument(self):
        "Logout with query string redirects to specified resource"
        self.login()
        response = self.client.post("/logout/?next=/login/")
        self.assertRedirects(response, "/login/", fetch_redirect_response=False)
        self.confirm_logged_out()