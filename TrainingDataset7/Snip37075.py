def safestring_in_template_exception(request):
    """
    Trigger an exception in the template machinery which causes a SafeString
    to be inserted as args[0] of the Exception.
    """
    template = Template('{% extends "<script>alert(1);</script>" %}')
    try:
        template.render(Context())
    except Exception:
        return technical_500_response(request, *sys.exc_info())