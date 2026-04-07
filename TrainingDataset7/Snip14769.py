def technical_500_response(request, exc_type, exc_value, tb, status_code=500):
    """
    Create a technical server error response. The last three arguments are
    the values returned from sys.exc_info() and friends.
    """
    reporter = get_exception_reporter_class(request)(request, exc_type, exc_value, tb)
    preferred_type = request.get_preferred_type(["text/html", "text/plain"])
    if preferred_type == "text/html":
        html = reporter.get_traceback_html()
        return HttpResponse(html, status=status_code, content_type="text/html")
    else:
        text = reporter.get_traceback_text()
        return HttpResponse(
            text, status=status_code, content_type="text/plain; charset=utf-8"
        )