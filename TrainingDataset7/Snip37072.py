def raises404(request):
    resolver = get_resolver(None)
    resolver.resolve("/not-in-urls")