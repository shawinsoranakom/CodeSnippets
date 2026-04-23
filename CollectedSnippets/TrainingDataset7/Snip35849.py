def test_resolver_match_on_request_before_resolution(self):
        request = HttpRequest()
        self.assertIsNone(request.resolver_match)