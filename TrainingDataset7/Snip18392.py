def test_redirect_param(self):
        """If next is specified as a GET parameter, go there."""
        self.login()
        url = self.do_redirect_url + "?next=/custom_next/"
        response = self.client.get(url)
        self.assertRedirects(response, "/custom_next/", fetch_redirect_response=False)