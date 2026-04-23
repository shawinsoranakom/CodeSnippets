def get_response(req):
            response = HttpResponse()
            response.headers["Content-Length"] = bad_content_length
            return response