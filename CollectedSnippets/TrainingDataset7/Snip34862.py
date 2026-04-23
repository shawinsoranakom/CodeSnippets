def set_session_view(request):
    "A view that sets a session variable"
    request.session["session_var"] = "YES"
    return HttpResponse("set_session")