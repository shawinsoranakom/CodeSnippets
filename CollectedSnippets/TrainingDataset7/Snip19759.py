def etag_view_weak(request):
    """
    Use an etag_func() that returns a weak ETag.
    """
    return HttpResponse(FULL_RESPONSE)