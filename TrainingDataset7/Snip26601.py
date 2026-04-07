def test_content_length_header_not_changed(self):
        bad_content_length = 500

        def get_response(req):
            response = HttpResponse()
            response.headers["Content-Length"] = bad_content_length
            return response

        response = CommonMiddleware(get_response)(self.rf.get("/"))
        self.assertEqual(int(response.headers["Content-Length"]), bad_content_length)