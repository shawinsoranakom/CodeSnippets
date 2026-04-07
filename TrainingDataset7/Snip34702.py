def get_host_view(request):
    return HttpResponse(request.get_host())