def post_view(request):
    """A view that expects a POST, and returns a different template depending
    on whether any POST data is available
    """
    if request.method == "POST":
        if request.POST:
            t = Template(
                "Data received: {{ data }} is the value.", name="POST Template"
            )
            c = Context({"data": request.POST["value"]})
        else:
            t = Template("Viewing POST page.", name="Empty POST Template")
            c = Context()
    else:
        t = Template("Viewing GET page.", name="Empty GET Template")
        # Used by test_body_read_on_get_data.
        request.read(200)
        c = Context()
    return HttpResponse(t.render(c))