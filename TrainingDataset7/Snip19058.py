def hello_world_view(request, value):
    return HttpResponse("Hello World %s" % value)