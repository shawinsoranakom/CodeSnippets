def deny_response(request):
            response = HttpResponse()
            response.headers["X-Frame-Options"] = "DENY"
            return response