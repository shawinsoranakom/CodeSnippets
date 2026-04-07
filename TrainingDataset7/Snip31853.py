def method_view(request):
    return HttpResponse(request.method)