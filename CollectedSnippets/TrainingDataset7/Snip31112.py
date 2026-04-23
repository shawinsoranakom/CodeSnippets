def test_copy(self):
        request = HttpRequest()
        request_copy = copy.copy(request)
        self.assertIs(request_copy.resolver_match, request.resolver_match)