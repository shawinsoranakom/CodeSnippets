def raises(request):
    # Make sure that a callable that raises an exception in the stack frame's
    # local vars won't hijack the technical 500 response (#15025).
    def callable():
        raise Exception

    try:
        raise Exception
    except Exception:
        return technical_500_response(request, *sys.exc_info())