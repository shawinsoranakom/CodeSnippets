def test_response_resolver_match_regular_view(self):
        """
        The response ResolverMatch instance contains the correct
        information when accessing a regular view.
        """
        response = self.client.get("/get_view/")
        self.assertEqual(response.resolver_match.url_name, "get_view")