def post_then_get_view(request):
    """
    A view that expects a POST request, returns a redirect response
    to itself providing only a ?success=true querystring,
    the value of this querystring is then rendered upon GET.
    """
    if request.method == "POST":
        return HttpResponseRedirect("?success=true")

    t = Template("The value of success is {{ value }}.", name="GET Template")
    c = Context({"value": request.GET.get("success", "false")})

    return HttpResponse(t.render(c))