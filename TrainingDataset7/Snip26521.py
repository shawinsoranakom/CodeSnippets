def show(request):
    template = engines["django"].from_string(TEMPLATE)
    return HttpResponse(template.render(request=request))