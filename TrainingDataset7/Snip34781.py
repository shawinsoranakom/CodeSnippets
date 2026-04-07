def test_redirect_scheme(self):
        """
        An assertion is raised if the response doesn't have the scheme
        specified in expected_url.
        """

        # For all possible True/False combinations of follow and secure
        for follow, secure in itertools.product([True, False], repeat=2):
            # always redirects to https
            response = self.client.get(
                "/https_redirect_view/", follow=follow, secure=secure
            )
            # the goal scheme is https
            self.assertRedirects(
                response, "https://testserver/secure_view/", status_code=302
            )
            with self.assertRaises(AssertionError):
                self.assertRedirects(
                    response, "http://testserver/secure_view/", status_code=302
                )