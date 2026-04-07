def redirect_based_on_extra_headers_2_view(request):
    if "HTTP_REDIRECT" in request.META:
        return HttpResponseRedirect("/redirects/further/more/")
    return HttpResponse()