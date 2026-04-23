def bad_view(request):
    "A view that returns a 404 with some error content"
    return HttpResponseNotFound("Not found!. This page contains some MAGIC content")