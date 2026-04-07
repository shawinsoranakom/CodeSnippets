def render_template_multiple_times(request):
    """A view that renders a template multiple times."""
    return HttpResponse(render_to_string("base.html") + render_to_string("base.html"))