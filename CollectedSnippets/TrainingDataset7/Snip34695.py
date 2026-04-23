def redirect_view(request):
    "A view that redirects all requests to the GET view"
    if request.GET:
        query = "?" + urlencode(request.GET, True)
    else:
        query = ""
    return HttpResponseRedirect("/get_view/" + query)