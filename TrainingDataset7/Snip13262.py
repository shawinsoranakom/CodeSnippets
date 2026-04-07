def csp(request):
    """
    Add the CSP nonce to the context.
    """
    return {"csp_nonce": get_nonce(request)}