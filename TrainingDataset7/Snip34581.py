def test_response_resolver_match(self):
        """
        The response contains a ResolverMatch instance.
        """
        response = self.client.get("/header_view/")
        self.assertTrue(hasattr(response, "resolver_match"))