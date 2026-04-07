def technical_404_response(request, exception):
    """Create a technical 404 error response. `exception` is the Http404."""
    try:
        error_url = exception.args[0]["path"]
    except (IndexError, TypeError, KeyError):
        error_url = request.path_info[1:]  # Trim leading slash

    try:
        tried = exception.args[0]["tried"]
    except (IndexError, TypeError, KeyError):
        resolved = True
        tried = request.resolver_match.tried if request.resolver_match else None
    else:
        resolved = False
        if not tried or (  # empty URLconf
            request.path_info == "/"
            and len(tried) == 1
            and len(tried[0]) == 1  # default URLconf
            and getattr(tried[0][0], "app_name", "")
            == getattr(tried[0][0], "namespace", "")
            == "admin"
        ):
            return default_urlconf(request)

    patterns_with_debug_info = []
    for urlpattern in tried or ():
        patterns = []
        for inner_pattern in urlpattern:
            wrapper = {"tried": inner_pattern}
            if isinstance(inner_pattern, URLResolver):
                wrapper["debug_key"] = "namespace"
                wrapper["debug_val"] = inner_pattern.namespace
            else:
                wrapper["debug_key"] = "name"
                wrapper["debug_val"] = inner_pattern.name
            patterns.append(wrapper)
        patterns_with_debug_info.append(patterns)

    urlconf = getattr(request, "urlconf", settings.ROOT_URLCONF)
    if isinstance(urlconf, types.ModuleType):
        urlconf = urlconf.__name__

    with builtin_template_path("technical_404.html").open(encoding="utf-8") as fh:
        t = DEBUG_ENGINE.from_string(fh.read())
    reporter_filter = get_default_exception_reporter_filter()
    c = Context(
        {
            "urlconf": urlconf,
            "root_urlconf": settings.ROOT_URLCONF,
            "request_path": error_url,
            "urlpatterns": tried,  # Unused, left for compatibility.
            "urlpatterns_debug": patterns_with_debug_info,
            "resolved": resolved,
            "reason": str(exception),
            "request": request,
            "settings": reporter_filter.get_safe_settings(),
            "raising_view_name": get_caller(request),
        }
    )
    return HttpResponseNotFound(t.render(c))