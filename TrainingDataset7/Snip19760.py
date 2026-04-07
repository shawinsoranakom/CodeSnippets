def etag_view_none(request):
    """
    Use an etag_func() that returns None, as opposed to setting etag_func=None.
    """
    return HttpResponse(FULL_RESPONSE)