def test_response_resolver_match_redirect_follow(self):
        """
        The response ResolverMatch instance contains the correct
        information when following redirects.
        """
        response = self.client.get("/redirect_view/", follow=True)
        self.assertEqual(response.resolver_match.url_name, "get_view")