def get_view(request):
    "A simple view that expects a GET request, and returns a rendered template"
    t = Template("This is a test. {{ var }} is the value.", name="GET Template")
    c = Context({"var": request.GET.get("var", 42)})

    return HttpResponse(t.render(c))