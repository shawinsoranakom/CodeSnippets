def test_logout_with_custom_redirect_argument(self):
        "Logout with custom query string redirects to specified resource"
        self.login()
        response = self.client.post("/logout/custom_query/?follow=/somewhere/")
        self.assertRedirects(response, "/somewhere/", fetch_redirect_response=False)
        self.confirm_logged_out()