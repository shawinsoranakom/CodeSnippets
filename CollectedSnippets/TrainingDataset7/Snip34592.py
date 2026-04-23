def test_permanent_redirect(self):
        "GET a URL that redirects permanently elsewhere"
        response = self.client.get("/permanent_redirect_view/")
        self.assertRedirects(response, "/get_view/", status_code=301)