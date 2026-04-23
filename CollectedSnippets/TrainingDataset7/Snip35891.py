def bad_view(request, *args, **kwargs):
    raise ValueError("I don't think I'm getting good value for this view")