def request_context_view(request):
    # Special attribute that won't be present on a plain HttpRequest
    request.special_path = request.path
    return render(request, "request_context.html")