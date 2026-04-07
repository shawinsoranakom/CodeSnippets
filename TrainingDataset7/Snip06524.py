def flatpage(request, url):
    """
    Public interface to the flat page view.

    Models: `flatpages.flatpages`
    Templates: Uses the template defined by the ``template_name`` field,
        or :template:`flatpages/default.html` if template_name is not defined.
    Context:
        flatpage
            `flatpages.flatpages` object
    """
    if not url.startswith("/"):
        url = "/" + url
    site_id = get_current_site(request).id
    try:
        f = get_object_or_404(FlatPage, url=url, sites=site_id)
    except Http404:
        if not url.endswith("/") and settings.APPEND_SLASH:
            url += "/"
            f = get_object_or_404(FlatPage, url=url, sites=site_id)
            return HttpResponsePermanentRedirect("%s/" % request.path)
        else:
            raise
    return render_flatpage(request, f)