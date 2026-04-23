def test_permanent_nonascii_redirect(self):
        """
        A non-ASCII argument to HttpPermanentRedirect is handled properly.
        """
        response = self.client.get("/permanent_nonascii_redirect/")
        self.assertRedirects(response, self.redirect_target, status_code=301)