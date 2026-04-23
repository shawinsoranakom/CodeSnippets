def same_origin_response(request):
            response = HttpResponse()
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            return response