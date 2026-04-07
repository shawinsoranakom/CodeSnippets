def condition(etag_func=None, last_modified_func=None):
    """
    Decorator to support conditional retrieval (or change) for a view
    function.

    The parameters are callables to compute the ETag and last modified time for
    the requested resource, respectively. The callables are passed the same
    parameters as the view itself. The ETag function should return a string (or
    None if the resource doesn't exist), while the last_modified function
    should return a datetime object (or None if the resource doesn't exist).

    The ETag function should return a complete ETag, including quotes (e.g.
    '"etag"'), since that's the only way to distinguish between weak and strong
    ETags. If an unquoted ETag is returned (e.g. 'etag'), it will be converted
    to a strong ETag by adding quotes.

    This decorator will either pass control to the wrapped view function or
    return an HTTP 304 response (unmodified) or 412 response (precondition
    failed), depending upon the request method. In either case, the decorator
    will add the generated ETag and Last-Modified headers to the response if
    the headers aren't already set and if the request's method is safe.
    """

    def decorator(func):
        def _pre_process_request(request, *args, **kwargs):
            # Compute values (if any) for the requested resource.
            res_last_modified = None
            if last_modified_func:
                if dt := last_modified_func(request, *args, **kwargs):
                    if not timezone.is_aware(dt):
                        dt = timezone.make_aware(dt, datetime.UTC)
                    res_last_modified = int(dt.timestamp())
            # The value from etag_func() could be quoted or unquoted.
            res_etag = etag_func(request, *args, **kwargs) if etag_func else None
            res_etag = quote_etag(res_etag) if res_etag is not None else None
            response = get_conditional_response(
                request,
                etag=res_etag,
                last_modified=res_last_modified,
            )
            return response, res_etag, res_last_modified

        def _post_process_request(request, response, res_etag, res_last_modified):
            # Set relevant headers on the response if they don't already exist
            # and if the request method is safe.
            if request.method in ("GET", "HEAD"):
                if res_last_modified and not response.has_header("Last-Modified"):
                    response.headers["Last-Modified"] = http_date(res_last_modified)
                if res_etag:
                    response.headers.setdefault("ETag", res_etag)

        if iscoroutinefunction(func):

            @wraps(func)
            async def inner(request, *args, **kwargs):
                response, res_etag, res_last_modified = _pre_process_request(
                    request, *args, **kwargs
                )
                if response is None:
                    response = await func(request, *args, **kwargs)
                _post_process_request(request, response, res_etag, res_last_modified)
                return response

        else:

            @wraps(func)
            def inner(request, *args, **kwargs):
                response, res_etag, res_last_modified = _pre_process_request(
                    request, *args, **kwargs
                )
                if response is None:
                    response = func(request, *args, **kwargs)
                _post_process_request(request, response, res_etag, res_last_modified)
                return response

        return inner

    return decorator