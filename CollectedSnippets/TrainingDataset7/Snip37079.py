def render_no_template(request):
    # If we do not specify a template, we need to make sure the debug
    # view doesn't blow up.
    return render(request, [], {})