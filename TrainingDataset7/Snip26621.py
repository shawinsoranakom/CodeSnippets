def test_no_etag_streaming_response(self):
        def get_response(req):
            return StreamingHttpResponse(["content"])

        self.assertFalse(
            ConditionalGetMiddleware(get_response)(self.req).has_header("ETag")
        )