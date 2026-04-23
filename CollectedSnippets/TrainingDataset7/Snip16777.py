def secure_view2(request):
    return HttpResponse(str(request.POST))