def test_copy_response(self):
        tests = ["/cbv_view/", "/get_view/"]
        for url in tests:
            with self.subTest(url=url):
                response = self.client.get(url)
                response_copy = copy.copy(response)
                self.assertEqual(repr(response), repr(response_copy))
                self.assertIs(response_copy.client, response.client)
                self.assertIs(response_copy.resolver_match, response.resolver_match)
                self.assertIs(response_copy.wsgi_request, response.wsgi_request)