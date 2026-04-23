def extract_views_from_urlpatterns(urlpatterns, base="", namespace=None):
    """
    Return a list of views from a list of urlpatterns.

    Each object in the returned list is a 4-tuple:
    (view_func, regex, namespace, name)
    """
    views = []
    for p in urlpatterns:
        if hasattr(p, "url_patterns"):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            views.extend(
                extract_views_from_urlpatterns(
                    patterns,
                    base + str(p.pattern),
                    (namespace or []) + (p.namespace and [p.namespace] or []),
                )
            )
        elif hasattr(p, "callback"):
            try:
                views.append((p.callback, base + str(p.pattern), namespace, p.name))
            except ViewDoesNotExist:
                continue
        else:
            raise TypeError(_("%s does not appear to be a urlpattern object") % p)
    return views