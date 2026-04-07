def get_response(req):
            response = HttpResponse("content")
            self.assertNotIn("Content-Length", response)
            return response