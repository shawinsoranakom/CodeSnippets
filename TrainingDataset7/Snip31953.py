def get_response_touching_session(request):
        request.session["hello"] = "world"
        return HttpResponse("Session test")