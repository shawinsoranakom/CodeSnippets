def sandwiched_rotate_token_view(request):
    """
    This is a view that calls rotate_token() in process_response() between two
    calls to CsrfViewMiddleware.process_response().
    """
    return TestingHttpResponse("OK")