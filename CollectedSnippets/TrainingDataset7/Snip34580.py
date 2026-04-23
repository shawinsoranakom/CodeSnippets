def test_response_attached_request(self):
        """
        The returned response has a ``request`` attribute with the originating
        environ dict and a ``wsgi_request`` with the originating WSGIRequest.
        """
        response = self.client.get("/header_view/")

        self.assertTrue(hasattr(response, "request"))
        self.assertTrue(hasattr(response, "wsgi_request"))
        for key, value in response.request.items():
            self.assertIn(key, response.wsgi_request.environ)
            self.assertEqual(response.wsgi_request.environ[key], value)