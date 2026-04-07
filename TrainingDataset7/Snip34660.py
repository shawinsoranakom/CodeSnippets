def test_request_factory(self):
        """The request factory implements all the HTTP/1.1 methods."""
        for method_name, view in self.http_methods_and_views:
            method = getattr(self.request_factory, method_name)
            request = method("/somewhere/")
            response = view(request)
            self.assertEqual(response.status_code, 200)