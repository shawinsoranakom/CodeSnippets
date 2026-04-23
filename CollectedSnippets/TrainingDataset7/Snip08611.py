def response_for_exception(request, exc):
    if isinstance(exc, Http404):
        if settings.DEBUG:
            response = debug.technical_404_response(request, exc)
        else:
            response = get_exception_response(
                request, get_resolver(get_urlconf()), 404, exc
            )

    elif isinstance(exc, PermissionDenied):
        response = get_exception_response(
            request, get_resolver(get_urlconf()), 403, exc
        )
        log_response(
            "Forbidden (Permission denied): %s",
            request.path,
            response=response,
            request=request,
            exception=exc,
        )

    elif isinstance(exc, MultiPartParserError):
        response = get_exception_response(
            request, get_resolver(get_urlconf()), 400, exc
        )
        log_response(
            "Bad request (Unable to parse request body): %s",
            request.path,
            response=response,
            request=request,
            exception=exc,
        )

    elif isinstance(exc, BadRequest):
        if settings.DEBUG:
            response = debug.technical_500_response(
                request, *sys.exc_info(), status_code=400
            )
        else:
            response = get_exception_response(
                request, get_resolver(get_urlconf()), 400, exc
            )
        log_response(
            "%s: %s",
            str(exc),
            request.path,
            response=response,
            request=request,
            exception=exc,
        )
    elif isinstance(exc, SuspiciousOperation):
        if isinstance(exc, (RequestDataTooBig, TooManyFieldsSent, TooManyFilesSent)):
            # POST data can't be accessed again, otherwise the original
            # exception would be raised.
            request._mark_post_parse_error()

        if settings.DEBUG:
            response = debug.technical_500_response(
                request, *sys.exc_info(), status_code=400
            )
        else:
            response = get_exception_response(
                request, get_resolver(get_urlconf()), 400, exc
            )
        # The logger is set to django.security, which specifically captures
        # SuspiciousOperation events, unlike the default django.request logger.
        security_logger = logging.getLogger(f"django.security.{exc.__class__.__name__}")
        log_response(
            str(exc),
            exception=exc,
            request=request,
            response=response,
            level="error",
            logger=security_logger,
        )

    else:
        signals.got_request_exception.send(sender=None, request=request)
        response = handle_uncaught_exception(
            request, get_resolver(get_urlconf()), sys.exc_info()
        )
        log_response(
            "%s: %s",
            response.reason_phrase,
            request.path,
            response=response,
            request=request,
            exception=exc,
        )

    # Force a TemplateResponse to be rendered.
    if not getattr(response, "is_rendered", True) and callable(
        getattr(response, "render", None)
    ):
        response = response.render()

    return response