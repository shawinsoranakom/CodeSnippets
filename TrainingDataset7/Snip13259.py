def static(request):
    """
    Add static-related context variables to the context.
    """
    return {"STATIC_URL": settings.STATIC_URL}