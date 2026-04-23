def test_streaming_response_not_contains_idempotent(self):
        response = StreamingHttpResponse(["hello world"])
        self.assertNotContains(response, "bye")
        self.assertNotContains(response, "bye")
        self.assertContains(response, "world")