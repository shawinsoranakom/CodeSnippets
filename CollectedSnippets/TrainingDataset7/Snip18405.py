def test_logout_with_next_page_specified(self):
        "Logout with next_page option given redirects to specified resource"
        self.login()
        response = self.client.post("/logout/next_page/")
        self.assertRedirects(response, "/somewhere/", fetch_redirect_response=False)
        self.confirm_logged_out()