def body(request):
    "A view that is requested with GET and accesses request.body. Refs #14753."
    return HttpResponse(request.body)