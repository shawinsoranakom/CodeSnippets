def test_httprequest_repr_invalid_method_and_path(self):
        request = HttpRequest()
        self.assertEqual(repr(request), "<HttpRequest>")
        request = HttpRequest()
        request.method = "GET"
        self.assertEqual(repr(request), "<HttpRequest>")
        request = HttpRequest()
        request.path = ""
        self.assertEqual(repr(request), "<HttpRequest>")