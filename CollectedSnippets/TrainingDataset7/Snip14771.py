def get_exception_reporter_filter(request):
    default_filter = get_default_exception_reporter_filter()
    return getattr(request, "exception_reporter_filter", default_filter)