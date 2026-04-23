def nested_view(request):
    """
    A view that uses test client to call another view.
    """
    c = Client()
    c.get("/no_template_view/")
    return render(request, "base.html", {"nested": "yes"})