def form_view(request):
    "A view that tests a simple form"
    if request.method == "POST":
        form = TestForm(request.POST)
        if form.is_valid():
            t = Template("Valid POST data.", name="Valid POST Template")
            c = Context()
        else:
            t = Template(
                "Invalid POST data. {{ form.errors }}", name="Invalid POST Template"
            )
            c = Context({"form": form})
    else:
        form = TestForm(request.GET)
        t = Template("Viewing base form. {{ form }}.", name="Form GET Template")
        c = Context({"form": form})

    return HttpResponse(t.render(c))