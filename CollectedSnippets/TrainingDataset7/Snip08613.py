def handle_uncaught_exception(request, resolver, exc_info):
    """
    Processing for any otherwise uncaught exceptions (those that will
    generate HTTP 500 responses).
    """
    if settings.DEBUG_PROPAGATE_EXCEPTIONS:
        raise

    if settings.DEBUG:
        return debug.technical_500_response(request, *exc_info)

    # Return an HttpResponse that displays a friendly error message.
    callback = resolver.resolve_error_handler(500)
    return callback(request)