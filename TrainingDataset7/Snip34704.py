def double_redirect_view(request):
    "A view that redirects all requests to a redirection view"
    return HttpResponseRedirect("/permanent_redirect_view/")