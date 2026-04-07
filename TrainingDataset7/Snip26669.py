def get_response(req):
            response = StreamingHttpResponse("content")
            self.assertNotIn("Content-Length", response)
            return response