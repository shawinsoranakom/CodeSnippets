def test_no_head(self):
        """
        ConditionalGetMiddleware shouldn't compute and return an ETag on a
        HEAD request since it can't do so accurately without access to the
        response body of the corresponding GET.
        """

        def get_200_response(req):
            return HttpResponse(status=200)

        request = self.request_factory.head("/")
        conditional_get_response = ConditionalGetMiddleware(get_200_response)(request)
        self.assertNotIn("ETag", conditional_get_response)