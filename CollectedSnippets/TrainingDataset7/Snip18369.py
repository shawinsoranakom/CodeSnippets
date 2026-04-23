def assertLoginURLEquals(self, url):
        response = self.client.get("/login_required/")
        self.assertRedirects(response, url, fetch_redirect_response=False)