def test_resolver_match_on_request(self):
        response = self.client.get("/resolver_match/")
        resolver_match = response.resolver_match
        self.assertEqual(resolver_match.url_name, "test-resolver-match")