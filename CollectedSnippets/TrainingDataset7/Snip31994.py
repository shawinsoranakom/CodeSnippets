def response_500(request):
            response = HttpResponse("Horrible error")
            response.status_code = 500
            request.session["hello"] = "world"
            return response