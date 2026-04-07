def csrf_token_error_handler(request, **kwargs):
    """This error handler accesses the CSRF token."""
    template = Template(get_token(request))
    return HttpResponse(template.render(Context()), status=599)