def test_redirect_with_lazy_reverse(self):
        response = self.client.get("/redirect/")
        self.assertRedirects(response, "/redirected_to/", status_code=302)