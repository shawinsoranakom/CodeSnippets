def pass_resolver_match_view(request, *args, **kwargs):
    response = HttpResponse()
    response.resolver_match = request.resolver_match
    return response