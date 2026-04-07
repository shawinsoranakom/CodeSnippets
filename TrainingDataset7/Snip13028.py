def get_nonce(request):
    return getattr(request, "_csp_nonce", None)