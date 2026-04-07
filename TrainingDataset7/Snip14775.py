def default_urlconf(request):
    """Create an empty URLconf 404 error response."""
    with builtin_template_path("default_urlconf.html").open(encoding="utf-8") as fh:
        t = DEBUG_ENGINE.from_string(fh.read())
    c = Context(
        {
            "version": get_docs_version(),
        }
    )

    return HttpResponse(t.render(c))