def internal_server_error(request):
    status = request.GET.get("status", 500)
    return HttpResponseServerError("Server Error", status=int(status))