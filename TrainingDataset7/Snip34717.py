def no_trailing_slash_external_redirect(request):
    """
    RFC 3986 Section 6.2.3: Empty path should be normalized to "/".

    Use https://testserver, rather than an external domain, in order to allow
    use of follow=True, triggering Client._handle_redirects().
    """
    return HttpResponseRedirect("https://testserver")