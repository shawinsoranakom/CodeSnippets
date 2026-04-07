def test_response_resolver_match_class_based_view(self):
        """
        The response ResolverMatch instance can be used to access the CBV view
        class.
        """
        response = self.client.get("/accounts/")
        self.assertIs(response.resolver_match.func.view_class, RedirectView)