def resolve(path, urlconf=None):
    if urlconf is None:
        urlconf = get_urlconf()
    return get_resolver(urlconf).resolve(path)