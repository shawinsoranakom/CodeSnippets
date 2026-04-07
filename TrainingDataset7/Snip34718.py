def index_view(request):
    """Target for no_trailing_slash_external_redirect with follow=True."""
    return HttpResponse("Hello world")