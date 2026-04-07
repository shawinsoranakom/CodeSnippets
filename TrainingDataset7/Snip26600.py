def test_content_length_header_not_added_for_streaming_response(self):
        def get_response(req):
            response = StreamingHttpResponse("content")
            self.assertNotIn("Content-Length", response)
            return response

        response = CommonMiddleware(get_response)(self.rf.get("/"))
        self.assertNotIn("Content-Length", response)