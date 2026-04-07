def get_caller(request):
    resolver_match = request.resolver_match
    if resolver_match is None:
        try:
            resolver_match = resolve(request.path)
        except Http404:
            pass
    return "" if resolver_match is None else resolver_match._func_path