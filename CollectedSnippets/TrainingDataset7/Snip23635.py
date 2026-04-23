def _assert_allows(self, response, *expected_methods):
        "Assert allowed HTTP methods reported in the Allow response header"
        response_allows = set(response.headers["Allow"].split(", "))
        self.assertEqual(set(expected_methods + ("OPTIONS",)), response_allows)