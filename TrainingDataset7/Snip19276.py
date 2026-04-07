def get_response(req):
            response = HttpResponse(content)
            response.set_cookie("foo", "bar")
            return response