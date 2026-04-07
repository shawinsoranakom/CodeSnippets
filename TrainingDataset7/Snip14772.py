def get_exception_reporter_class(request):
    default_exception_reporter_class = import_string(
        settings.DEFAULT_EXCEPTION_REPORTER
    )
    return getattr(
        request, "exception_reporter_class", default_exception_reporter_class
    )