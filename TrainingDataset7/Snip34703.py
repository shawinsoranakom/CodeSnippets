def view_with_secure(request):
    "A view that indicates if the request was secure"
    response = HttpResponse()
    response.test_was_secure_request = request.is_secure()
    response.test_server_port = request.META.get("SERVER_PORT", 80)
    return response