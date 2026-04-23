def test_get_request_from_factory(self):
        """
        The request factory returns a templated response for a GET request.
        """
        request = self.request_factory.get("/somewhere/")
        response = get_view(request)
        self.assertContains(response, "This is a test")