def get_response(req):
            response = HttpResponse(self.compressible_string)
            response.headers["ETag"] = '"eggs"'
            return response