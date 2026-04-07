def custom_reporter_class_view(request):
    request.exception_reporter_class = CustomExceptionReporter
    try:
        raise Exception
    except Exception:
        exc_info = sys.exc_info()
        return technical_500_response(request, *exc_info)