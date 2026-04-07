def assertLoginRedirectURLEqual(self, url):
        response = self.login()
        self.assertRedirects(response, url, fetch_redirect_response=False)