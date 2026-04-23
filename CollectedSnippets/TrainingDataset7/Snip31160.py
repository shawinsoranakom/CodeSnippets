def params_view(request, slug):
    return HttpResponse(f"Params: {slug}")