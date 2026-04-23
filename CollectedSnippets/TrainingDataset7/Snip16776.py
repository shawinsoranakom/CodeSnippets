def secure_view(request):
    return HttpResponse(str(request.POST))