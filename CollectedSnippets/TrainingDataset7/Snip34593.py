def test_temporary_redirect(self):
        "GET a URL that does a non-permanent redirect"
        response = self.client.get("/temporary_redirect_view/")
        self.assertRedirects(response, "/get_view/", status_code=302)