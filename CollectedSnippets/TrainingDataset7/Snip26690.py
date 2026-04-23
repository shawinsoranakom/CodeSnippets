def get_response(req):
            response = HttpResponse(self.compressible_string)
            response.headers["ETag"] = 'W/"eggs"'
            return response