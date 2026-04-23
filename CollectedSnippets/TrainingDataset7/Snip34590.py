def test_redirect_with_query(self):
        "GET a URL that redirects with given GET parameters"
        response = self.client.get("/redirect_view/", {"var": "value"})
        self.assertRedirects(response, "/get_view/?var=value")