def test_redirect_to_strange_location(self):
        "GET a URL that redirects to a non-200 page"
        response = self.client.get("/double_redirect_view/")
        # The response was a 302, and that the attempt to get the redirection
        # location returned 301 when retrieved
        self.assertRedirects(
            response, "/permanent_redirect_view/", target_status_code=301
        )