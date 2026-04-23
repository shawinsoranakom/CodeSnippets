def csrf_view(request):
    return HttpResponse(csrf(request)["csrf_token"])