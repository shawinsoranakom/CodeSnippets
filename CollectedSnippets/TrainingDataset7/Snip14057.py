def _get_cached_resolver(urlconf=None):
    return URLResolver(RegexPattern(r"^/"), urlconf)