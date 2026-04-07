def csp_nonce(request):
    return HttpResponse(get_nonce(request))