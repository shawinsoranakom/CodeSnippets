def test_redirect_with_query_ordering(self):
        """assertRedirects() ignores the order of query string parameters."""
        response = self.client.get("/redirect_view/", {"var": "value", "foo": "bar"})
        self.assertRedirects(response, "/get_view/?var=value&foo=bar")
        self.assertRedirects(response, "/get_view/?foo=bar&var=value")