def test_response_resolver_match_middleware_urlconf(self):
        response = self.client.get("/middleware_urlconf_view/")
        self.assertEqual(response.resolver_match.url_name, "middleware_urlconf_view")