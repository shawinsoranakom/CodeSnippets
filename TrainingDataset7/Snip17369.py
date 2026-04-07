def hello(request):
    name = request.GET.get("name") or "World"
    return HttpResponse("Hello %s!" % name)