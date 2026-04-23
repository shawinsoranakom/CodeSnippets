def test_follow_relative_redirect_no_trailing_slash(self):
        """
        A URL with a relative redirect with no trailing slash can be followed.
        """
        response = self.client.get("/accounts/no_trailing_slash", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request["PATH_INFO"], "/accounts/login/")