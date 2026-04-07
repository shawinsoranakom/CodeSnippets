def csrf(request):
    """
    Context processor that provides a CSRF token, or the string 'NOTPROVIDED'
    if it has not been provided by either a view decorator or the middleware
    """

    def _get_val():
        token = get_token(request)
        if token is None:
            # In order to be able to provide debugging info in the
            # case of misconfiguration, we use a sentinel value
            # instead of returning an empty dict.
            return "NOTPROVIDED"
        else:
            return token

    return {"csrf_token": SimpleLazyObject(_get_val)}