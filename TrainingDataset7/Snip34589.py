def test_redirect(self):
        "GET a URL that redirects elsewhere"
        response = self.client.get("/redirect_view/")
        self.assertRedirects(response, "/get_view/")