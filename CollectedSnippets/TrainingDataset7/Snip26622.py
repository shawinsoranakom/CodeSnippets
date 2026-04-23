def test_no_etag_response_empty_content(self):
        def get_response(req):
            return HttpResponse()

        self.assertFalse(
            ConditionalGetMiddleware(get_response)(self.req).has_header("ETag")
        )