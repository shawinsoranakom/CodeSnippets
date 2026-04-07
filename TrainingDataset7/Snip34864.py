def request_methods_view(request):
    "A view that responds with the request method"
    return HttpResponse("request method: %s" % request.method)