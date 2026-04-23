def test_streaming_response_idempotent(self):
        response = StreamingHttpResponse(["hello world"])
        self.assertContains(response, "hello")
        self.assertContains(response, "world")