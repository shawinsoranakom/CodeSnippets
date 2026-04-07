def read_all(request):
    "A view that is requested with accesses request.read()."
    return HttpResponse(request.read())