def test_content_length_header_added(self):
        def get_response(req):
            response = HttpResponse("content")
            self.assertNotIn("Content-Length", response)
            return response

        response = CommonMiddleware(get_response)(self.rf.get("/"))
        self.assertEqual(int(response.headers["Content-Length"]), len(response.content))