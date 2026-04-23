def test_options(self):
        """
        Views respond to HTTP OPTIONS requests with an Allow header
        appropriate for the methods implemented by the view class.
        """
        request = self.rf.options("/")
        view = SimpleView.as_view()
        response = view(request)
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.headers["Allow"])