def get_token(request):
    """
    Return the CSRF token required for a POST form. The token is an
    alphanumeric value. A new token is created if one is not already set.

    A side effect of calling this function is to make the csrf_protect
    decorator and the CsrfViewMiddleware add a CSRF cookie and a 'Vary: Cookie'
    header to the outgoing response. For this reason, you may need to use this
    function lazily, as is done by the csrf context processor.
    """
    if "CSRF_COOKIE" in request.META:
        csrf_secret = request.META["CSRF_COOKIE"]
        # Since the cookie is being used, flag to send the cookie in
        # process_response() (even if the client already has it) in order to
        # renew the expiry timer.
        request.META["CSRF_COOKIE_NEEDS_UPDATE"] = True
    else:
        csrf_secret = _add_new_csrf_cookie(request)
    return _mask_cipher_secret(csrf_secret)