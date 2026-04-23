def etag_view_unquoted(request):
    """
    Use an etag_func() that returns an unquoted ETag.
    """
    return HttpResponse(FULL_RESPONSE)