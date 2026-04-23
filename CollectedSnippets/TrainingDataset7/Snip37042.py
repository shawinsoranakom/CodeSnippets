def test_nonascii_redirect(self):
        """
        A non-ASCII argument to HttpRedirect is handled properly.
        """
        response = self.client.get("/nonascii_redirect/")
        self.assertRedirects(response, self.redirect_target)