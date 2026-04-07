def redirect_based_on_extra_headers_1_view(request):
    if "HTTP_REDIRECT" in request.META:
        return HttpResponseRedirect("/redirect_based_on_extra_headers_2/")
    return HttpResponse()