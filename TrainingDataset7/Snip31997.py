def response_ending_session(request):
            request.session.flush()
            return HttpResponse("Session test")