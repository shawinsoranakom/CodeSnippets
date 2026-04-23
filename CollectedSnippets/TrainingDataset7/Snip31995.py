def response_503(request):
            response = HttpResponse("Service Unavailable")
            response.status_code = 503
            request.session["hello"] = "world"
            return response