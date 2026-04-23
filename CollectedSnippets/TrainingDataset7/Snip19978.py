def csp_nonce_processor(request):
    return render(request, "context_processors/csp_nonce.html")