def response_set_session(request):
            # Set a session key and some data.
            request.session["foo"] = "bar"
            return HttpResponse("Session test")