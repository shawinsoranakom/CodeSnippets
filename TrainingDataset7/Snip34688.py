def trace_view(request):
    """
    A simple view that expects a TRACE request and echoes its status line.

    TRACE requests should not have an entity; the view will return a 400 status
    response if it is present.
    """
    if request.method.upper() != "TRACE":
        return HttpResponseNotAllowed("TRACE")
    elif request.body:
        return HttpResponseBadRequest("TRACE requests MUST NOT include an entity")
    else:
        protocol = request.META["SERVER_PROTOCOL"]
        t = Template(
            "{{ method }} {{ uri }} {{ version }}",
            name="TRACE Template",
        )
        c = Context(
            {
                "method": request.method,
                "uri": request.path,
                "version": protocol,
            }
        )
        return HttpResponse(t.render(c))