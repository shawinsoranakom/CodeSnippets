def read_buffer(request):
    "A view that is requested with accesses request.read(LARGE_BUFFER)."
    return HttpResponse(request.read(99999))