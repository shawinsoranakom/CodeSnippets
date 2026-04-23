def json_view(request):
    """
    A view that expects a request with the header 'application/json' and JSON
    data, which is deserialized and included in the context.
    """
    if request.META.get("CONTENT_TYPE") != "application/json":
        return HttpResponse()

    t = Template("Viewing {} page. With data {{ data }}.".format(request.method))
    data = json.loads(request.body.decode("utf-8"))
    c = Context({"data": data})
    return HttpResponse(t.render(c))