def get_exception_response(request, resolver, status_code, exception):
    try:
        callback = resolver.resolve_error_handler(status_code)
        response = callback(request, exception=exception)
    except Exception:
        signals.got_request_exception.send(sender=None, request=request)
        response = handle_uncaught_exception(request, resolver, sys.exc_info())

    return response