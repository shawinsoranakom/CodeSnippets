def check_session_view(request):
    "A view that reads a session variable"
    return HttpResponse(request.session.get("session_var", "NO"))