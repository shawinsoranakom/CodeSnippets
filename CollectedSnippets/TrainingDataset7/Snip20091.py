def token_view(request):
    context = RequestContext(request, processors=[csrf])
    template = Template("{% csrf_token %}")
    return HttpResponse(template.render(context))